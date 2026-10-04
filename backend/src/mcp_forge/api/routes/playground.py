"""Playground API routes for session management, tool execution, and SSE event streaming."""

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.api.deps import require_auth
from mcp_forge.db.session import get_db_session
from mcp_forge.playground.manager import get_session_manager

router = APIRouter(
    prefix="/api/playground", tags=["Playground"], dependencies=[Depends(require_auth)]
)


class CreateSessionRequest(BaseModel):
    """Payload to launch a new playground session."""

    build_id: str
    target: str = Field(default="mock")  # mock | live
    env_vars: dict[str, str] = Field(default_factory=dict)


class ToolCallRequest(BaseModel):
    """Payload to invoke a tool within an active session."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    timeout_s: float = Field(default=30.0)


async def get_db(request: Request) -> AsyncGenerator[AsyncSession]:
    """Dependency for obtaining an async DB session."""
    settings = request.app.state.settings
    async with get_db_session(settings) as session:
        yield session


@router.post("/sessions")
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    principal: str = Depends(require_auth),
) -> dict[str, Any]:
    """Launch a new isolated playground session."""
    manager = get_session_manager()
    session_model = await manager.create_session(
        db_session=db,
        build_id=body.build_id,
        target=body.target,
        user_env_vars=body.env_vars,
        owner_principal=principal,
    )
    return {
        "id": session_model.id,
        "session_id": session_model.id,
        "build_id": session_model.build_id,
        "target": session_model.target,
        "status": session_model.status,
        "started_at": session_model.started_at,
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    principal: str = Depends(require_auth),
) -> dict[str, Any]:
    """Get active session status and info."""
    manager = get_session_manager()
    active = manager.get_session(session_id, caller_principal=principal)
    return {
        "id": active.session_id,
        "build_id": active.build_id,
        "target": active.target,
        "status": "running",
        "created_at": active.created_at,
        "last_active": active.last_active_ts,
    }


@router.get("/sessions/{session_id}/tools")
async def list_session_tools(
    session_id: str,
    principal: str = Depends(require_auth),
) -> dict[str, Any]:
    """List available tools exposed by the session's server."""
    manager = get_session_manager()
    active = manager.get_session(session_id, caller_principal=principal)
    tools = await active.client.list_tools()
    return {"tools": tools}


@router.post("/sessions/{session_id}/call")
async def call_session_tool(
    session_id: str,
    body: ToolCallRequest,
    principal: str = Depends(require_auth),
) -> dict[str, Any]:
    """Invoke an MCP tool through the playground session."""
    manager = get_session_manager()
    active = manager.get_session(session_id, caller_principal=principal)
    result = await active.client.call_tool(
        name=body.name,
        arguments=body.arguments,
        timeout_s=body.timeout_s,
    )
    return result


@router.get("/sessions/{session_id}/trace")
async def stream_session_trace(
    session_id: str,
    request: Request,
    principal: str = Depends(require_auth),
) -> StreamingResponse:
    """Stream real-time protocol trace events via Server-Sent Events (SSE)."""
    manager = get_session_manager()
    active = manager.get_session(session_id, caller_principal=principal)

    async def event_generator() -> Any:
        # First yield past recorded events
        for ev in list(active.trace.events):
            yield f"data: {json.dumps(ev)}\n\n"

        queue = active.trace.subscribe()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(ev)}\n\n"
                except TimeoutError:
                    # Keep-alive comment
                    yield ": keep-alive\n\n"
        finally:
            active.trace.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    principal: str = Depends(require_auth),
) -> dict[str, Any]:
    """Stop and terminate an active playground session."""
    manager = get_session_manager()
    await manager.stop_session(
        db,
        session_id,
        exit_info="User requested stop",
        caller_principal=principal,
    )
    return {"status": "stopped", "session_id": session_id}
