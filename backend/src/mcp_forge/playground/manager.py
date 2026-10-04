"""Playground session manager: limits, session tracking, mock/live targets, and background cleanup.

Deployment Architecture Note:
Active playground sessions, subprocess references, and stdio pipes are process-local in-memory state.
MCP Forge runs as a single-process server (1 uvicorn worker). Multi-worker deployments (e.g. uvicorn -w 4)
are not supported for interactive playground sessions as child subprocess handles cannot be shared across
separate OS processes without an external supervisor daemon.
"""

import asyncio
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from mcp_forge.config import get_settings
from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.db.models.build import Build
from mcp_forge.db.models.playground_session import PlaygroundSession
from mcp_forge.db.models.trace_event import TraceEvent
from mcp_forge.db.uuid_helper import utcnow_iso, uuidv7
from mcp_forge.errors import ConflictError, ForbiddenError, ForgeError, NotFoundError
from mcp_forge.mock_api.server import MockServer
from mcp_forge.playground.client import PlaygroundClient
from mcp_forge.playground.sandbox import SandboxLauncher
from mcp_forge.playground.trace import TraceRecorder
from mcp_forge.services.builds import resolve_build_paths


class ActiveSession:
    """In-memory representation of an active process-isolated playground session."""

    def __init__(
        self,
        session_id: str,
        build_id: str,
        target: str,
        client: PlaygroundClient,
        trace: TraceRecorder,
        mock_server: MockServer | None = None,
        owner_principal: str = "local",
    ) -> None:
        self.session_id = session_id
        self.build_id = build_id
        self.target = target
        self.client = client
        self.trace = trace
        self.mock_server = mock_server
        self.owner_principal = owner_principal
        self.last_active_ts = time.time()
        self.created_at = time.time()

    def touch(self) -> None:
        self.last_active_ts = time.time()


class SessionManager:
    """Manages active process-isolated Playground sessions with concurrency limits and cleanup."""

    def __init__(self) -> None:
        self._active_sessions: dict[str, ActiveSession] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: asyncio.Task[None] | None = None

    @property
    def active_count(self) -> int:
        return len(self._active_sessions)

    def get_session(self, session_id: str, caller_principal: str | None = None) -> ActiveSession:
        if session_id not in self._active_sessions:
            raise NotFoundError(f"Active playground session '{session_id}' not found.")
        s = self._active_sessions[session_id]
        if caller_principal and caller_principal != "local" and s.owner_principal != "local":
            if s.owner_principal != caller_principal:
                raise ForbiddenError(
                    "You do not have permission to access this playground session."
                )
        s.touch()
        return s

    async def create_session(
        self,
        db_session: AsyncSession,
        build_id: str,
        target: str = "mock",  # mock | live
        user_env_vars: dict[str, str] | None = None,
        owner_principal: str = "local",
    ) -> PlaygroundSession:
        """Create a new playground session with isolation and concurrency checks."""
        settings = get_settings()

        # 1. Check if playground is enabled
        if settings.playground_enabled is False:
            raise ForgeError(
                "Playground is disabled by configuration.",
                code="PLAYGROUND_DISABLED",
                status_code=403,
            )

        async with self._lock:
            # 2. Check concurrency cap
            if len(self._active_sessions) >= settings.playground_max_sessions:
                raise ConflictError(
                    f"Maximum concurrent playground sessions ({settings.playground_max_sessions}) reached. "
                    "Please stop an existing session first.",
                )

            # 3. Retrieve build with eager loaded project and spec_version
            stmt_build = (
                select(Build)
                .options(joinedload(Build.project), joinedload(Build.spec_version))
                .where(Build.id == build_id)
            )
            res_build = await db_session.execute(stmt_build)
            build = res_build.scalar_one_or_none()

            if not build:
                raise NotFoundError(f"Build with ID '{build_id}' not found.")
            if build.status != "succeeded":
                raise ConflictError(f"Cannot test build with status '{build.status}'.")

            # Locate server directory using canonical resolver
            server_dir, _ = resolve_build_paths(build, build.project.slug)
            if not server_dir.exists():
                raise NotFoundError(f"Generated server directory '{server_dir}' not found on disk.")

            session_id = uuidv7()
            user_env_vars = user_env_vars or {}
            mock_server: MockServer | None = None
            base_url_override: str | None = None

            # 4. If target is mock, start in-process mock server
            if target == "mock":
                raw_text = build.spec_version.raw_text
                parsed = parse_and_validate(raw_text)
                ir = normalize_spec(parsed)
                mock_server = MockServer(ir)
                base_url_override = await mock_server.start()

            # 5. Extract secrets for trace redaction
            secret_values = set(user_env_vars.values())

            # 6. Setup trace recorder and sandbox launcher
            trace = TraceRecorder(session_id=session_id, extra_secrets=secret_values)
            sandbox = SandboxLauncher(
                server_dir=server_dir,
                user_env_vars=user_env_vars,
                base_url_override=base_url_override,
            )

            client = PlaygroundClient(sandbox=sandbox, trace=trace)

            # Connect client to server with guaranteed cleanup on startup failure
            try:
                await client.connect()
            except Exception:
                await client.disconnect()
                sandbox.terminate()
                if mock_server:
                    await mock_server.stop()
                raise

            # Store in database
            db_model = PlaygroundSession(
                id=session_id,
                build_id=build_id,
                target=target,
                status="running",
                started_at=utcnow_iso(),
            )
            db_session.add(db_model)
            await db_session.commit()
            await db_session.refresh(db_model)

            # Store in memory
            active = ActiveSession(
                session_id=session_id,
                build_id=build_id,
                target=target,
                client=client,
                trace=trace,
                mock_server=mock_server,
                owner_principal=owner_principal,
            )
            self._active_sessions[session_id] = active

            return db_model

    async def stop_session(
        self,
        db_session: AsyncSession,
        session_id: str,
        exit_info: str | None = None,
        caller_principal: str | None = None,
    ) -> None:
        """Stop and clean up an active session."""
        async with self._lock:
            active = self._active_sessions.get(session_id)
            if (
                active
                and caller_principal
                and caller_principal != "local"
                and active.owner_principal != "local"
            ):
                if active.owner_principal != caller_principal:
                    raise ForbiddenError(
                        "You do not have permission to terminate this playground session."
                    )
            active = self._active_sessions.pop(session_id, None)
        if active:
            # Disconnect client
            await active.client.disconnect()

            # Terminate sandbox
            active.client.sandbox.terminate()

            # Stop mock server if any
            if active.mock_server:
                await active.mock_server.stop()

            # Persist trace events to database
            for ev in active.trace.events:
                db_ev = TraceEvent(
                    session_id=session_id,
                    seq=ev["seq"],
                    direction=ev["direction"],
                    message_json=ev["message_json"],
                    duration_ms=ev.get("duration_ms"),
                )
                db_session.add(db_ev)

        # Update database record
        db_model = await db_session.get(PlaygroundSession, session_id)
        if db_model:
            db_model.status = "stopped"
            db_model.ended_at = utcnow_iso()
            if exit_info:
                db_model.exit_info = exit_info
            await db_session.commit()

    async def cleanup_all(self, db_session: AsyncSession) -> None:
        """Stop all active sessions on shutdown."""
        session_ids = list(self._active_sessions.keys())
        for sid in session_ids:
            try:
                await self.stop_session(db_session, sid, exit_info="Server shutdown")
            except Exception:  # noqa: S110
                pass


# Global session manager instance
_session_manager: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Return singleton session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
