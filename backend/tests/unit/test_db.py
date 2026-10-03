"""Unit tests for database models, migrations, and retention policies."""

import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select

from mcp_forge.config import Settings
from mcp_forge.db.models.app_setting import AppSetting
from mcp_forge.db.models.build import Build
from mcp_forge.db.models.operation_config import OperationConfig
from mcp_forge.db.models.playground_session import PlaygroundSession
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.review_finding import ReviewFinding
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.db.models.trace_event import TraceEvent
from mcp_forge.db.session import get_db_session, purge_old_traces
from mcp_forge.db.uuid_helper import uuidv7


def test_uuidv7_format_and_ordering() -> None:
    id1 = uuidv7()
    id2 = uuidv7()
    # Must be valid UUIDs
    u1 = uuid.UUID(id1)
    u2 = uuid.UUID(id2)
    assert u1.version == 7
    assert u2.version == 7
    # Time-ordered
    assert id1 <= id2


def test_alembic_migrations_upgrade_and_downgrade(tmp_path: Path) -> None:
    db_file = tmp_path / "test_migration.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # 1. Upgrade to head
    command.upgrade(alembic_cfg, "head")
    assert db_file.exists()

    # 2. Downgrade to base
    command.downgrade(alembic_cfg, "base")

    # 3. Re-upgrade to head
    command.upgrade(alembic_cfg, "head")


@pytest.mark.asyncio
async def test_models_lifecycle_and_cascades(tmp_path: Path) -> None:
    db_file = tmp_path / "test_lifecycle.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    test_settings = Settings(
        forge_mode="local",
        forge_host="127.0.0.1",
        forge_data_dir=tmp_path,
        database_url=db_url,
    )

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    async with get_db_session(test_settings) as session:
        # 1. Create project
        proj = Project(name="Petstore API", slug="petstore-api")
        session.add(proj)
        await session.flush()

        # 2. Add ProjectSettings
        settings = ProjectSettings(
            project_id=proj.id,
            base_url="https://api.petstore.com/v1",
        )
        session.add(settings)

        # 3. Add SpecVersion
        spec = SpecVersion(
            project_id=proj.id,
            version_no=1,
            source_type="file",
            source_ref="petstore.yaml",
            format="yaml",
            spec_kind="oas30",
            sha256="abc1234567890",
            raw_text="openapi: 3.0.0\ninfo:\n  title: Petstore\n",
            operation_count=10,
        )
        session.add(spec)
        await session.flush()

        # 4. Add OperationConfig
        op_cfg = OperationConfig(
            project_id=proj.id,
            operation_key="GET /pets",
            enabled=True,
            tool_name_override="list_pets",
        )
        session.add(op_cfg)

        # 5. Add Build
        build = Build(
            project_id=proj.id,
            spec_version_id=spec.id,
            build_no=1,
            status="succeeded",
            tool_count=5,
            warning_count=0,
            generator_version="0.1.0",
            artifact_path="/artifacts/build-1.zip",
            artifact_sha256="buildsha123",
        )
        session.add(build)
        await session.flush()

        # 6. Add ReviewFinding
        finding = ReviewFinding(
            project_id=proj.id,
            spec_version_id=spec.id,
            build_id=build.id,
            severity="warning",
            code="QUAL-001",
            message="Short description",
        )
        session.add(finding)

        # 7. Add PlaygroundSession & TraceEvent
        pg_session = PlaygroundSession(
            build_id=build.id,
            target="mock",
            status="running",
        )
        session.add(pg_session)
        await session.flush()

        trace = TraceEvent(
            session_id=pg_session.id,
            seq=1,
            direction="client_to_server",
            message_json='{"jsonrpc": "2.0", "method": "tools/list"}',
        )
        session.add(trace)

        # 8. Add AppSetting
        app_set = AppSetting(key="retention_days", value="7")
        session.add(app_set)

    # Verify query and relationships
    async with get_db_session(test_settings) as session:
        result = await session.execute(select(Project).where(Project.slug == "petstore-api"))
        fetched_proj = result.scalar_one()
        assert fetched_proj.name == "Petstore API"

        # Verify cascades when project is deleted
        await session.delete(fetched_proj)

    # Verify children were cascaded
    async with get_db_session(test_settings) as session:
        specs_res = await session.execute(select(SpecVersion))
        assert specs_res.scalars().all() == []

        builds_res = await session.execute(select(Build))
        assert builds_res.scalars().all() == []


@pytest.mark.asyncio
async def test_trace_retention_purge(tmp_path: Path) -> None:
    db_file = tmp_path / "test_retention.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    test_settings = Settings(
        forge_mode="local",
        forge_host="127.0.0.1",
        forge_data_dir=tmp_path,
        database_url=db_url,
    )

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    async with get_db_session(test_settings) as session:
        proj = Project(name="Test Ret", slug="test-ret")
        session.add(proj)
        await session.flush()

        spec = SpecVersion(
            project_id=proj.id,
            version_no=1,
            source_type="file",
            source_ref="spec.json",
            format="json",
            spec_kind="oas30",
            sha256="sha",
            raw_text="{}",
        )
        session.add(spec)
        await session.flush()

        build = Build(
            project_id=proj.id,
            spec_version_id=spec.id,
            build_no=1,
            status="succeeded",
            generator_version="0.1.0",
            artifact_path="art",
            artifact_sha256="sha",
        )
        session.add(build)
        await session.flush()

        pg_session = PlaygroundSession(build_id=build.id, target="mock", status="stopped")
        session.add(pg_session)
        await session.flush()

        # Old trace event (10 days ago)
        old_trace = TraceEvent(
            session_id=pg_session.id,
            seq=1,
            direction="server_to_client",
            message_json='{"status": "old"}',
            created_at="2020-01-01T00:00:00Z",
        )
        # Recent trace event
        recent_trace = TraceEvent(
            session_id=pg_session.id,
            seq=2,
            direction="server_to_client",
            message_json='{"status": "recent"}',
            created_at="2099-01-01T00:00:00Z",
        )
        session.add_all([old_trace, recent_trace])

    async with get_db_session(test_settings) as session:
        deleted_count = await purge_old_traces(session, retention_days=7)
        assert deleted_count == 1

        remaining = (await session.execute(select(TraceEvent))).scalars().all()
        assert len(remaining) == 1
        assert remaining[0].seq == 2
