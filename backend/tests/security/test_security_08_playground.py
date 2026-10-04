"""Security test 08: Playground sandbox environment scrubbing, concurrency limits, and process cleanup."""

import hashlib
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from mcp_forge.config import Settings
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.db.session import get_db_session, reset_engine
from mcp_forge.errors import ConflictError
from mcp_forge.playground.manager import SessionManager
from mcp_forge.playground.sandbox import SandboxLauncher
from mcp_forge.services.builds import create_build_for_project

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


def test_sandbox_launcher_environment_scrubbing(tmp_path: Path) -> None:
    """Sandbox environment inherits only minimal safe OS variables, redirects HOME/TEMP, and adds user credentials."""
    dummy_server_dir = tmp_path / "server"
    dummy_server_dir.mkdir()

    launcher = SandboxLauncher(
        server_dir=dummy_server_dir,
        user_env_vars={"MY_SECRET_API_KEY": "secret_val_123"},
        base_url_override="http://127.0.0.1:9999",
    )
    launcher.temp_dir = tmp_path / "scratch"
    launcher.temp_dir.mkdir()

    env = launcher.build_scrubbed_env()

    # User supplied credentials present in process env
    assert env["MY_SECRET_API_KEY"] == "secret_val_123"
    assert env["API_BASE_URL"] == "http://127.0.0.1:9999"
    assert env["MCP_TRANSPORT"] == "stdio"

    # HOME / TEMP redirected to scratch temp dir
    assert env["HOME"] == str(launcher.temp_dir)

    # PYTHONPATH includes server_dir
    assert str(dummy_server_dir.resolve()) in env["PYTHONPATH"]


@pytest.mark.asyncio
async def test_session_manager_concurrency_cap_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Security test 08: Session manager enforces concurrency limit and terminates sessions cleanly."""
    await reset_engine()
    db_file = tmp_path / "test_playground.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    test_settings = Settings(
        forge_mode="local",
        forge_host="127.0.0.1",
        forge_data_dir=tmp_path / "data",
        database_url=db_url,
        playground_max_sessions=1,  # Set concurrency cap to 1
    )
    monkeypatch.setattr("mcp_forge.services.builds.get_settings", lambda: test_settings)
    monkeypatch.setattr("mcp_forge.playground.manager.get_settings", lambda: test_settings)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    raw_text = (SAMPLE_DIR / "bookshop.openapi.yaml").read_text(encoding="utf-8")
    sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    async with get_db_session(test_settings) as session:
        # Create project, spec version, and build
        proj = Project(name="Bookshop API", slug="bookshop")
        session.add(proj)
        await session.flush()

        settings_obj = ProjectSettings(project_id=proj.id, base_url="https://api.bookshop.com")
        session.add(settings_obj)

        spec_ver = SpecVersion(
            project_id=proj.id,
            version_no=1,
            source_type="sample",
            source_ref="bookshop.openapi.yaml",
            format="yaml",
            spec_kind="oas30",
            sha256=sha256,
            raw_text=raw_text,
            operation_count=5,
        )
        session.add(spec_ver)
        await session.commit()

        build = await create_build_for_project(session, project_id=proj.id)
        assert build.status == "succeeded"

        manager = SessionManager()

        # 1. Create session 1
        s1 = await manager.create_session(session, build_id=build.id, target="mock")
        assert s1.status == "running"
        assert manager.active_count == 1

        # Verify session can list tools
        active1 = manager.get_session(s1.id)
        tools = await active1.client.list_tools()
        assert len(tools) > 0

        # Verify trace has recorded client and server messages
        assert len(active1.trace.events) > 0

        # 2. Creating session 2 should violate concurrency cap (max 1) and raise ConflictError
        with pytest.raises(ConflictError, match="Maximum concurrent playground sessions"):
            await manager.create_session(session, build_id=build.id, target="mock")

        # 3. Stop session 1
        await manager.stop_session(session, s1.id)
        assert manager.active_count == 0

        # 4. Now session 2 can be created
        s2 = await manager.create_session(session, build_id=build.id, target="mock")
        assert manager.active_count == 1
        await manager.stop_session(session, s2.id)
        assert manager.active_count == 0


@pytest.mark.asyncio
async def test_session_manager_ownership_enforcement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify session manager enforces caller principal ownership in exposed mode."""
    from mcp_forge.errors import ForbiddenError

    await reset_engine()
    db_file = tmp_path / "test_ownership.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    test_settings = Settings(
        forge_mode="exposed",
        forge_host="127.0.0.1",
        forge_access_token="test-secret-token-32-chars-long",
        forge_data_dir=tmp_path / "data",
        database_url=db_url,
        playground_enabled=True,
        playground_max_sessions=5,
    )
    monkeypatch.setattr("mcp_forge.services.builds.get_settings", lambda: test_settings)
    monkeypatch.setattr("mcp_forge.playground.manager.get_settings", lambda: test_settings)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    raw_text = (SAMPLE_DIR / "bookshop.openapi.yaml").read_text(encoding="utf-8")
    sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    async with get_db_session(test_settings) as session:
        proj = Project(name="Bookshop API", slug="bookshop-owner")
        session.add(proj)
        await session.flush()

        settings_obj = ProjectSettings(project_id=proj.id, base_url="https://api.bookshop.com")
        session.add(settings_obj)

        spec_ver = SpecVersion(
            project_id=proj.id,
            version_no=1,
            source_type="sample",
            source_ref="bookshop.openapi.yaml",
            format="yaml",
            spec_kind="oas30",
            sha256=sha256,
            raw_text=raw_text,
            operation_count=5,
        )
        session.add(spec_ver)
        await session.commit()

        build = await create_build_for_project(session, project_id=proj.id)

        manager = SessionManager()
        s = await manager.create_session(
            session, build_id=build.id, target="mock", owner_principal="user_alice"
        )

        # Owner user_alice can access
        active = manager.get_session(s.id, caller_principal="user_alice")
        assert active.session_id == s.id

        # Non-owner user_bob is rejected with ForbiddenError
        with pytest.raises(ForbiddenError):
            manager.get_session(s.id, caller_principal="user_bob")

        with pytest.raises(ForbiddenError):
            await manager.stop_session(session, s.id, caller_principal="user_bob")

        # Owner can stop the session
        await manager.stop_session(session, s.id, caller_principal="user_alice")
        assert manager.active_count == 0

        # Double stop is safe and idempotent
        await manager.stop_session(session, s.id, caller_principal="user_alice")
        assert manager.active_count == 0


def test_sandbox_launcher_stderr_draining(tmp_path: Path) -> None:
    """SandboxLauncher background thread continuously drains stderr into bounded ring buffer."""
    server_dir = tmp_path / "dummy_server"
    server_dir.mkdir()
    # Write a script that emits to stderr
    (server_dir / "server.py").write_text(
        "import sys\nfor i in range(5):\n    sys.stderr.write(f'log line {i}\\n')\nsys.stderr.flush()\n",
        encoding="utf-8",
    )

    launcher = SandboxLauncher(server_dir=server_dir)
    proc = launcher.start()
    proc.wait(timeout=5.0)

    # Let thread drain
    if launcher._drain_thread:
        launcher._drain_thread.join(timeout=2.0)

    assert len(launcher.stderr_lines) > 0
    assert any("log line" in line for line in launcher.stderr_lines)
    launcher.terminate()
    assert launcher.temp_dir is None


def test_sandbox_launcher_missing_server_cleanup(tmp_path: Path) -> None:
    """Missing server.py raises FileNotFoundError without leaving orphaned directories."""
    empty_dir = tmp_path / "empty_server"
    empty_dir.mkdir()
    launcher = SandboxLauncher(server_dir=empty_dir)

    with pytest.raises(FileNotFoundError):
        launcher.start()

    launcher.terminate()
    assert launcher.temp_dir is None


def test_sandbox_launcher_prevents_env_override(tmp_path: Path) -> None:
    """SandboxLauncher prevents hostile user env vars from overriding critical runtime settings."""
    empty_dir = tmp_path / "server_dir"
    empty_dir.mkdir()

    launcher = SandboxLauncher(
        server_dir=empty_dir,
        user_env_vars={
            "PYTHONPATH": "/malicious/override",
            "PATH": "/malicious/bin",
            "MCP_TRANSPORT": "malicious",
            "API_BASE_URL": "http://evil.com",
            "VALID_API_KEY": "secret-12345",
            "123INVALID": "bad-key",
        },
    )
    env = launcher.build_scrubbed_env()

    # Protected keys must NOT be overridden by user
    assert env["MCP_TRANSPORT"] == "stdio"
    assert "/malicious/override" not in env["PYTHONPATH"]
    assert env.get("PATH") != "/malicious/bin"
    # Malformed keys rejected
    assert "123INVALID" not in env
    # Legitimate credentials preserved
    assert env["VALID_API_KEY"] == "secret-12345"
