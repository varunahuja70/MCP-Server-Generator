"""Comprehensive tests for Forge REST API routes:

- Samples (list, create project from sample)
- Projects (CRUD, slug collision, delete confirmation)
- Specs (upload, paste, preservation across versions, diff)
- Operations (list with risk labels, bulk update, presets)
- Settings (get, update)
- Review (trigger findings, acknowledge)
- Builds (generate, file tree, file content, download, connect snippets)
- Auth and Security Test 10 (exposed mode token, session cookie, 401 on missing auth)
"""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from mcp_forge.api.app import create_app
from mcp_forge.config import Settings
from mcp_forge.db.session import reset_engine
from mcp_forge.errors import UnsafeConfigError

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


@pytest.fixture
async def api_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> AsyncGenerator[tuple[AsyncClient, Settings]]:
    """Setup clean SQLite DB with Alembic migrations and local mode settings."""
    await reset_engine()
    db_file = tmp_path / "test_api.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    test_settings = Settings(
        forge_mode="local",
        forge_host="127.0.0.1",
        forge_port=8080,
        forge_data_dir=tmp_path / "data",
        database_url=db_url,
    )
    monkeypatch.setattr("mcp_forge.services.builds.get_settings", lambda: test_settings)
    monkeypatch.setattr("mcp_forge.playground.manager.get_settings", lambda: test_settings)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    app = create_app(test_settings)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://127.0.0.1:8080",
        headers={"Host": "127.0.0.1:8080", "X-Forge-Request": "1"},
    ) as client:
        yield client, test_settings


@pytest.mark.asyncio
async def test_samples_and_create_project_from_sample(
    api_env: tuple[AsyncClient, Settings],
) -> None:
    client, _ = api_env

    # 1. List samples
    res = await client.get("/api/samples")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) >= 3
    sample_ids = [s["id"] for s in samples]
    assert "bookshop" in sample_ids
    assert "tasks" in sample_ids

    # 2. Create project from sample
    res_proj = await client.post("/api/samples/create-project", json={"sample_id": "bookshop"})
    assert res_proj.status_code == 200
    proj_data = res_proj.json()
    assert proj_data["name"] == "Bookshop API"
    assert proj_data["slug"] == "bookshop-sample"
    assert proj_data["spec_version_count"] == 1
    assert proj_data["operation_count"] > 0


@pytest.mark.asyncio
async def test_projects_crud_and_delete_confirmation(
    api_env: tuple[AsyncClient, Settings],
) -> None:
    client, _ = api_env

    # 1. Create project
    res = await client.post("/api/projects", json={"name": "My Unique Project", "slug": "my-proj"})
    assert res.status_code == 200
    proj = res.json()
    proj_id = proj["id"]
    assert proj["slug"] == "my-proj"

    # 2. Slug collision
    res_dup = await client.post("/api/projects", json={"name": "Duplicate", "slug": "my-proj"})
    assert res_dup.status_code == 409

    # 3. List projects
    res_list = await client.get("/api/projects")
    assert res_list.status_code == 200
    assert any(p["id"] == proj_id for p in res_list.json())

    # 4. Get project
    res_get = await client.get(f"/api/projects/{proj_id}")
    assert res_get.status_code == 200
    assert res_get.json()["slug"] == "my-proj"

    # 5. Patch project
    res_patch = await client.patch(f"/api/projects/{proj_id}", json={"name": "Renamed Project"})
    assert res_patch.status_code == 200
    assert res_patch.json()["name"] == "Renamed Project"

    # 6. Delete project with incorrect slug confirmation fails
    res_del_bad = await client.request(
        "DELETE", f"/api/projects/{proj_id}", json={"confirm_slug": "wrong-slug"}
    )
    assert res_del_bad.status_code == 400

    # 7. Delete project with matching slug succeeds
    res_del_ok = await client.request(
        "DELETE", f"/api/projects/{proj_id}", json={"confirm_slug": "my-proj"}
    )
    assert res_del_ok.status_code == 200
    assert res_del_ok.json()["status"] == "deleted"

    # Verify 404 after delete
    res_after = await client.get(f"/api/projects/{proj_id}")
    assert res_after.status_code == 404


@pytest.mark.asyncio
async def test_specs_selection_preservation_and_diff(
    api_env: tuple[AsyncClient, Settings],
) -> None:
    client, _ = api_env

    # Create project from sample
    res_proj = await client.post("/api/samples/create-project", json={"sample_id": "bookshop"})
    proj_id = res_proj.json()["id"]

    # Check operations default selection
    res_ops = await client.get(f"/api/projects/{proj_id}/operations")
    assert res_ops.status_code == 200
    ops_data = res_ops.json()
    assert ops_data["total_count"] > 0
    # Enable a write operation explicitly
    write_op = next(o for o in ops_data["operations"] if o["risk"] == "write")
    op_key = write_op["operation_key"]

    res_up = await client.put(
        f"/api/projects/{proj_id}/operations",
        json={
            "operations": [
                {
                    "operation_key": op_key,
                    "enabled": True,
                    "tool_name_override": "custom_write_tool",
                }
            ]
        },
    )
    assert res_up.status_code == 200

    # Ingest a second spec version (same spec text with a modification)
    raw_text = (SAMPLES_DIR / "bookshop.openapi.yaml").read_text(encoding="utf-8")
    mod_text = raw_text.replace("Bookshop API", "Bookshop API v2")

    res_spec2 = await client.post(
        f"/api/projects/{proj_id}/specs",
        json={"source_type": "paste", "content": mod_text, "filename": "bookshop-v2.yaml"},
    )
    assert res_spec2.status_code == 200
    v2_data = res_spec2.json()
    assert v2_data["version_no"] == 2

    # Verify that the user's operation override and enabled choice was PRESERVED across spec versions
    res_ops2 = await client.get(f"/api/projects/{proj_id}/operations")
    op_after = next(o for o in res_ops2.json()["operations"] if o["operation_key"] == op_key)
    assert op_after["enabled"] is True
    assert op_after["tool_name"] == "custom_write_tool"

    # Test spec diff endpoint
    res_diff = await client.get(f"/api/projects/{proj_id}/specs/1/diff?against=2")
    assert res_diff.status_code == 200
    diff_report = res_diff.json()
    assert diff_report["title_changed"] is True
    assert diff_report["base_version_no"] == 1
    assert diff_report["target_version_no"] == 2


@pytest.mark.asyncio
async def test_operations_presets_and_settings(
    api_env: tuple[AsyncClient, Settings],
) -> None:
    client, _ = api_env

    res_proj = await client.post("/api/samples/create-project", json={"sample_id": "tasks"})
    proj_id = res_proj.json()["id"]

    # Apply 'none' preset
    res_none = await client.post(
        f"/api/projects/{proj_id}/operations/preset", json={"preset": "none"}
    )
    assert res_none.status_code == 200
    res_ops = await client.get(f"/api/projects/{proj_id}/operations")
    assert res_ops.json()["enabled_count"] == 0

    # Apply 'read-only' preset
    res_ro = await client.post(
        f"/api/projects/{proj_id}/operations/preset", json={"preset": "read-only"}
    )
    assert res_ro.status_code == 200
    res_ops_ro = await client.get(f"/api/projects/{proj_id}/operations")
    assert res_ops_ro.json()["enabled_count"] == res_ops_ro.json()["read_count"]

    # Settings get & update
    res_sett = await client.get(f"/api/projects/{proj_id}/settings")
    assert res_sett.status_code == 200
    assert res_sett.json()["timeout_s"] == 30

    res_sett_up = await client.put(
        f"/api/projects/{proj_id}/settings",
        json={"timeout_s": 45, "tool_prefix": "app", "retry_safe_requests": False},
    )
    assert res_sett_up.status_code == 200
    assert res_sett_up.json()["timeout_s"] == 45
    assert res_sett_up.json()["tool_prefix"] == "app"
    assert res_sett_up.json()["retry_safe_requests"] is False


@pytest.mark.asyncio
async def test_review_and_builds_pipeline(
    api_env: tuple[AsyncClient, Settings],
) -> None:
    client, _ = api_env

    res_proj = await client.post("/api/samples/create-project", json={"sample_id": "bookshop"})
    proj_id = res_proj.json()["id"]

    # Trigger review
    res_rev = await client.post(f"/api/projects/{proj_id}/review")
    assert res_rev.status_code == 200
    rev_data = res_rev.json()
    assert "findings" in rev_data

    # Acknowledge findings if any blocking errors exist
    if rev_data["has_blocking_errors"]:
        codes = [f["code"] for f in rev_data["findings"] if f["severity"] == "error"]
        res_ack = await client.post(
            f"/api/projects/{proj_id}/review/acknowledge",
            json={"finding_codes": codes},
        )
        assert res_ack.status_code == 200

    # Trigger build
    res_b = await client.post(f"/api/projects/{proj_id}/builds")
    assert res_b.status_code == 200
    b_data = res_b.json()
    assert b_data["status"] == "succeeded"
    build_id = b_data["id"]

    # Get build summary
    res_b_get = await client.get(f"/api/builds/{build_id}")
    assert res_b_get.status_code == 200
    assert res_b_get.json()["status"] == "succeeded"

    # Get file tree
    res_tree = await client.get(f"/api/builds/{build_id}/files")
    assert res_tree.status_code == 200
    tree = res_tree.json()
    assert len(tree) > 0
    file_names = [item["name"] for item in tree]
    assert "tools.json" in file_names
    assert "server.py" in file_names

    # Get file content
    res_content = await client.get(f"/api/builds/{build_id}/files/content?path=tools.json")
    assert res_content.status_code == 200
    assert "tools" in res_content.json()["content"]

    # Connect snippets
    res_conn = await client.get(f"/api/builds/{build_id}/connect")
    assert res_conn.status_code == 200
    snippets = res_conn.json()
    assert "claude_desktop" in snippets
    assert "cli_stdio" in snippets

    # Download archive
    res_dl = await client.get(f"/api/builds/{build_id}/download")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/zip"
    assert len(res_dl.content) > 0


@pytest.mark.asyncio
async def test_security_10_exposed_mode_auth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Security Test 10: Exposed mode requires token; unauthenticated calls get 401; login sets cookie."""
    # 1. Exposed mode refuses to start without token
    with pytest.raises(UnsafeConfigError):
        Settings(
            forge_mode="exposed",
            forge_host="0.0.0.0",
            forge_access_token=None,  # Missing
        )

    with pytest.raises(UnsafeConfigError):
        Settings(
            forge_mode="exposed",
            forge_host="0.0.0.0",
            forge_access_token="short",  # < 16 chars
        )

    # 2. Exposed mode with valid token starts properly
    valid_token = "secret-super-secure-token-12345678"
    db_file = tmp_path / "test_exposed.sqlite3"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    exposed_settings = Settings(
        forge_mode="exposed",
        forge_host="0.0.0.0",
        forge_public_host="forge.example.com",
        forge_access_token=valid_token,
        forge_data_dir=tmp_path / "data",
        database_url=db_url,
    )
    monkeypatch.setattr("mcp_forge.services.builds.get_settings", lambda: exposed_settings)
    monkeypatch.setattr("mcp_forge.playground.manager.get_settings", lambda: exposed_settings)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")

    app = create_app(exposed_settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://forge.example.com:8080",
        headers={"Host": "forge.example.com:8080", "X-Forge-Request": "1"},
    ) as client:
        # Healthz is exempt from authentication
        res_h = await client.get("/healthz")
        assert res_h.status_code == 200

        # Protected route without auth returns 401
        res_unauth = await client.get("/api/projects")
        assert res_unauth.status_code == 401
        assert res_unauth.json()["error"]["code"] == "UNAUTHORIZED"

        # Protected route with wrong Bearer token returns 401
        res_bad_tok = await client.get(
            "/api/projects", headers={"Authorization": "Bearer wrong-token"}
        )
        assert res_bad_tok.status_code == 401

        # Protected route with valid Bearer token succeeds
        res_good_tok = await client.get(
            "/api/projects", headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert res_good_tok.status_code == 200

        # Login endpoint with wrong token returns 401
        res_login_bad = await client.post("/api/auth/login", json={"token": "bad-pass"})
        assert res_login_bad.status_code == 401

        # Login endpoint with valid token sets session cookie
        res_login_ok = await client.post("/api/auth/login", json={"token": valid_token})
        assert res_login_ok.status_code == 200
        assert "forge_session" in res_login_ok.cookies

        # Subsequent requests using the session cookie succeed without Authorization header
        session_cookie = res_login_ok.cookies["forge_session"]
        res_cookie_auth = await client.get(
            "/api/projects", headers={"Cookie": f"forge_session={session_cookie}"}
        )
        assert res_cookie_auth.status_code == 200

        # Auth status confirms authentication via cookie
        res_status = await client.get(
            "/api/auth/status", headers={"Cookie": f"forge_session={session_cookie}"}
        )
        assert res_status.status_code == 200
        assert res_status.json()["authenticated"] is True

        # Logout revokes session cookie
        res_logout = await client.post(
            "/api/auth/logout", headers={"Cookie": f"forge_session={session_cookie}"}
        )
        assert res_logout.status_code == 200

        # Post-logout request with old cookie fails with 401
        res_after_logout = await client.get(
            "/api/projects", headers={"Cookie": f"forge_session={session_cookie}"}
        )
        assert res_after_logout.status_code == 401


@pytest.mark.asyncio
async def test_project_delete_cleans_build_artifacts_on_disk(
    api_env: tuple[AsyncClient, Settings],
) -> None:
    client, settings = api_env

    # Create project and generate build
    res_proj = await client.post("/api/samples/create-project", json={"sample_id": "bookshop"})
    proj_id = res_proj.json()["id"]
    slug = res_proj.json()["slug"]

    # Trigger build
    res_b = await client.post(f"/api/projects/{proj_id}/builds")
    assert res_b.status_code == 200

    builds_on_disk = settings.forge_data_dir / "builds" / slug
    assert builds_on_disk.exists(), "Build artifacts directory should exist after build"

    # Delete project with confirmation
    res_del = await client.request(
        "DELETE", f"/api/projects/{proj_id}", json={"confirm_slug": slug}
    )
    assert res_del.status_code == 200

    # Ensure build artifacts directory was cleaned up
    assert not builds_on_disk.exists(), (
        "Build artifacts on disk should be removed upon project deletion"
    )


@pytest.mark.asyncio
async def test_review_scoping_to_spec_version(
    api_env: tuple[AsyncClient, Settings],
) -> None:
    client, _ = api_env

    # Create empty project
    res_proj = await client.post(
        "/api/projects", json={"name": "Review Scope Test", "slug": "scope-test"}
    )
    proj_id = res_proj.json()["id"]

    # Add v1 spec
    spec_v1 = """openapi: "3.0.0"
info:
  title: "API V1"
  version: "1.0.0"
paths: {}
"""
    res_s1 = await client.post(
        f"/api/projects/{proj_id}/specs", json={"source_type": "paste", "content": spec_v1}
    )
    assert res_s1.status_code == 200
    v1_id = res_s1.json()["id"]
    assert v1_id is not None

    # Add v2 spec
    spec_v2 = """openapi: "3.0.0"
info:
  title: "API V2"
  version: "2.0.0"
paths: {}
"""
    res_s2 = await client.post(
        f"/api/projects/{proj_id}/specs", json={"source_type": "paste", "content": spec_v2}
    )
    assert res_s2.status_code == 200
    v2_id = res_s2.json()["id"]

    # Review project (targets latest, which is v2)
    res_rev = await client.post(f"/api/projects/{proj_id}/review")
    assert res_rev.status_code == 200

    # Acknowledging with explicit spec_version_id=v2_id scopes to v2 only
    res_ack = await client.post(
        f"/api/projects/{proj_id}/review/acknowledge",
        json={"finding_codes": ["SPEC-001"], "spec_version_id": v2_id},
    )
    assert res_ack.status_code == 200
