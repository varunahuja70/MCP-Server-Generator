"""Unit tests for packaging (deterministic zip) and builds service."""

import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from mcp_forge.config import Settings
from mcp_forge.core.render.package import create_deterministic_zip
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.db.session import get_db_session, reset_engine
from mcp_forge.errors import ForgeError, NotFoundError
from mcp_forge.services.builds import (
    create_build_for_project,
    generate_client_snippets,
    get_build_file_content,
    list_build_file_tree,
)

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


def test_deterministic_zip_reproducibility(tmp_path: Path) -> None:
    """Packaging the same source directory produces byte-identical zip archives with matching sha256."""
    src_dir = tmp_path / "source"
    src_dir.mkdir()
    (src_dir / "file_b.txt").write_text("Hello B", encoding="utf-8")
    (src_dir / "file_a.txt").write_text("Hello A", encoding="utf-8")
    subdir = src_dir / "subdir"
    subdir.mkdir()
    (subdir / "sub_file.txt").write_text("Nested content", encoding="utf-8")

    zip1_path = tmp_path / "archive1.zip"
    zip2_path = tmp_path / "archive2.zip"

    _, sha1 = create_deterministic_zip(src_dir, zip1_path)
    _, sha2 = create_deterministic_zip(src_dir, zip2_path)

    assert sha1 == sha2
    assert zip1_path.read_bytes() == zip2_path.read_bytes()

    # Check zip contents are ordered and have fixed timestamps
    with zipfile.ZipFile(zip1_path, "r") as zf:
        infolist = zf.infolist()
        filenames = [info.filename for info in infolist]
        assert filenames == sorted(filenames)
        for info in infolist:
            assert info.date_time == (2026, 1, 1, 0, 0, 0)


def test_generate_client_snippets() -> None:
    """Connection snippets format claude desktop, cursor, cli stdio, and http correctly."""
    snippets = generate_client_snippets(
        project_slug="petstore",
        server_dir="/app/servers/petstore",
        required_env_vars=["API_KEY"],
    )

    claude_cfg = json.loads(snippets["claude_desktop"])
    assert "petstore-mcp" in claude_cfg["mcpServers"]
    assert claude_cfg["mcpServers"]["petstore-mcp"]["env"] == {"API_KEY": "${API_KEY}"}

    cursor_cfg = json.loads(snippets["cursor"])
    assert "petstore-mcp" in cursor_cfg["mcpServers"]

    assert "server.py" in snippets["cli_stdio"]
    assert "petstore" in snippets["cli_stdio"]
    assert "--http" in snippets["cli_http"]
    assert snippets["required_env_vars"] == ["API_KEY"]


def test_list_build_file_tree_and_get_content(tmp_path: Path) -> None:
    """Tree traversal and safe file content reading work as expected."""
    project_dir = tmp_path / "my_project"
    project_dir.mkdir()
    (project_dir / "server.py").write_text("print('test')", encoding="utf-8")
    sub = project_dir / "runtime"
    sub.mkdir()
    (sub / "config.py").write_text("DEBUG = True", encoding="utf-8")

    tree = list_build_file_tree(project_dir)
    assert len(tree) == 2

    content = get_build_file_content(project_dir, "server.py")
    assert content == "print('test')"

    sub_content = get_build_file_content(project_dir, "runtime/config.py")
    assert sub_content == "DEBUG = True"

    with pytest.raises(NotFoundError):
        get_build_file_content(project_dir, "nonexistent.py")

    with pytest.raises(ForgeError) as exc_info:
        get_build_file_content(project_dir, "../outside.txt")
    assert exc_info.value.code == "PATH_TRAVERSAL_DETECTED"


@pytest.mark.asyncio
async def test_build_sample_specs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Builds for bundled sample specs succeed, store artifacts, and match checksums."""
    await reset_engine()
    db_file = tmp_path / "test_builds.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    test_settings = Settings(
        forge_mode="local",
        forge_host="127.0.0.1",
        forge_data_dir=tmp_path / "data",
        database_url=db_url,
    )
    monkeypatch.setattr("mcp_forge.services.builds.get_settings", lambda: test_settings)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    samples = [
        ("bookshop", "bookshop.openapi.yaml", "oas30", "yaml"),
        ("tasks", "tasks.openapi.json", "oas31", "json"),
        ("legacy", "legacy-swagger2.json", "swagger2", "json"),
    ]

    for slug, filename, kind, fmt in samples:
        spec_path = SAMPLE_DIR / filename
        assert spec_path.exists(), f"Sample {filename} missing"
        raw_text = spec_path.read_text(encoding="utf-8")
        sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        async with get_db_session(test_settings) as session:
            # 1. Create project
            proj = Project(name=f"Sample {slug.title()}", slug=slug)
            session.add(proj)
            await session.flush()

            # 2. Add ProjectSettings
            settings_obj = ProjectSettings(
                project_id=proj.id,
                base_url="https://api.example.com",
            )
            session.add(settings_obj)

            # 3. Add SpecVersion
            spec_ver = SpecVersion(
                project_id=proj.id,
                version_no=1,
                source_type="sample",
                source_ref=filename,
                format=fmt,
                spec_kind=kind,
                sha256=sha256,
                raw_text=raw_text,
                operation_count=5,
            )
            session.add(spec_ver)
            await session.commit()

            # 4. Run build
            build = await create_build_for_project(session, project_id=proj.id)

            assert build.status == "succeeded", f"Build failed: {build.error_message_safe}"
            assert build.tool_count > 0
            assert build.artifact_sha256 != ""
            assert Path(build.artifact_path).exists()

            # Verify artifact zip file
            zip_p = Path(build.artifact_path)
            with open(zip_p, "rb") as f:
                actual_sha = hashlib.sha256(f.read()).hexdigest()
            assert actual_sha == build.artifact_sha256

            # Verify tools.json inside zip
            with zipfile.ZipFile(zip_p, "r") as zf:
                assert "tools.json" in zf.namelist()
                assert "server.py" in zf.namelist()
                tools_data = json.loads(zf.read("tools.json").decode("utf-8"))
                assert len(tools_data["tools"]) == build.tool_count
