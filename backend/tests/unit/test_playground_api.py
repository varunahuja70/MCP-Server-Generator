"""Integration and endpoint tests for Playground backend."""

import hashlib
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from mcp_forge.api.app import create_app
from mcp_forge.config import Settings
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.db.session import get_db_session, reset_engine
from mcp_forge.services.builds import create_build_for_project

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


@pytest.mark.asyncio
async def test_playground_routes_lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Full lifecycle: create session via API, list tools, call tool, and delete session."""
    await reset_engine()
    db_file = tmp_path / "test_api_playground.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    test_settings = Settings(
        forge_mode="local",
        forge_host="127.0.0.1",
        forge_data_dir=tmp_path / "data",
        database_url=db_url,
    )
    monkeypatch.setattr("mcp_forge.services.builds.get_settings", lambda: test_settings)
    monkeypatch.setattr("mcp_forge.playground.manager.get_settings", lambda: test_settings)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    raw_text = (SAMPLE_DIR / "bookshop.openapi.yaml").read_text(encoding="utf-8")
    sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    # Create build
    async with get_db_session(test_settings) as session:
        proj = Project(name="Bookshop Playground API", slug="bookshop-pg")
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
        build_id = build.id

    app = create_app(test_settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://127.0.0.1:8080",
        headers={"Host": "127.0.0.1:8080", "X-Forge-Request": "1"},
    ) as client:
        # 1. Create session
        res_create = await client.post(
            "/api/playground/sessions",
            json={"build_id": build_id, "target": "mock", "env_vars": {"TEST_KEY": "val123"}},
        )
        assert res_create.status_code == 200
        session_data = res_create.json()
        session_id = session_data["id"]
        assert session_data["status"] == "running"

        # 2. Get session status
        res_get = await client.get(f"/api/playground/sessions/{session_id}")
        assert res_get.status_code == 200
        assert res_get.json()["target"] == "mock"

        # 3. List tools
        res_tools = await client.get(f"/api/playground/sessions/{session_id}/tools")
        assert res_tools.status_code == 200
        tools = res_tools.json()["tools"]
        assert len(tools) > 0
        first_tool_name = tools[0]["name"]

        # 4. Call tool
        res_call = await client.post(
            f"/api/playground/sessions/{session_id}/call",
            json={"name": first_tool_name, "arguments": {}},
        )
        assert res_call.status_code == 200
        call_json = res_call.json()
        assert "content" in call_json

        # 5. Stop session
        res_del = await client.delete(f"/api/playground/sessions/{session_id}")
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "stopped"
