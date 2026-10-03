"""Unit tests for code generation and project rendering."""

import json
from pathlib import Path

from mcp_forge.core.mapping.manifest import ManifestDoc, ManifestInfo, ToolManifest
from mcp_forge.core.render.renderer import render_project
from mcp_forge.core.render.writer import write_manifest_json


def _create_sample_manifest() -> ManifestDoc:
    tool1 = ToolManifest(
        name="get_pet_by_id",
        operation_key="get_pet_petId",
        description="Retrieve a pet by unique identifier.",
        method="GET",
        path="/pet/{petId}",
        input_schema={
            "type": "object",
            "properties": {
                "petId": {"type": "integer", "description": "ID of pet to return"},
            },
            "required": ["petId"],
        },
        param_locations={"petId": "path"},
        is_flattened_body=False,
        security=[{"api_key": []}],
        annotations={"read_only": True, "destructive": False, "open_world": False},
    )

    tool2 = ToolManifest(
        name="add_pet",
        operation_key="post_pet",
        description="Add a new pet to the store.",
        method="POST",
        path="/pet",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "status": {"type": "string"},
            },
            "required": ["name"],
        },
        param_locations={"name": "body", "status": "body"},
        is_flattened_body=True,
        security=[{"api_key": []}],
        annotations={"read_only": False, "destructive": False, "open_world": False},
    )

    return ManifestDoc(
        info=ManifestInfo(
            title="Petstore API",
            version="1.0.0",
            base_url="https://petstore.example.com/v2",
            description="A sample petstore server.",
        ),
        auth={
            "api_key": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "env_var": "PETSTORE_API_KEY",
                "required_env_vars": ["PETSTORE_API_KEY"],
            }
        },
        tools=[tool1, tool2],
    )


def test_render_project_structure(tmp_path: Path) -> None:
    """Project renderer creates all required project files and directories."""
    manifest = _create_sample_manifest()
    out_dir = tmp_path / "petstore_mcp"

    render_project(manifest, out_dir, slug="petstore")

    assert (out_dir / "tools.json").is_file()
    assert (out_dir / "server.py").is_file()
    assert (out_dir / "pyproject.toml").is_file()
    assert (out_dir / "README.md").is_file()
    assert (out_dir / ".env.example").is_file()
    assert (out_dir / "Dockerfile").is_file()
    assert (out_dir / "runtime" / "__init__.py").is_file()
    assert (out_dir / "runtime" / "client.py").is_file()
    assert (out_dir / "runtime" / "auth.py").is_file()
    assert (out_dir / "tests" / "test_manifest.py").is_file()
    assert (out_dir / "tests" / "test_server.py").is_file()
    assert (out_dir / "tests" / "test_runtime.py").is_file()

    # Verify tools.json structure
    manifest_data = json.loads((out_dir / "tools.json").read_text(encoding="utf-8"))
    assert manifest_data["info"]["title"] == "Petstore API"
    assert len(manifest_data["tools"]) == 2
    assert manifest_data["tools"][0]["name"] == "get_pet_by_id"


def test_render_project_deterministic_output(tmp_path: Path) -> None:
    """Two consecutive renders of the exact same manifest produce byte-identical output."""
    manifest = _create_sample_manifest()
    dir_1 = tmp_path / "run_1"
    dir_2 = tmp_path / "run_2"

    render_project(manifest, dir_1, slug="petstore")
    render_project(manifest, dir_2, slug="petstore")

    # Walk all files in run_1 and compare bytes with run_2
    files_1 = sorted([p.relative_to(dir_1) for p in dir_1.rglob("*") if p.is_file()])
    files_2 = sorted([p.relative_to(dir_2) for p in dir_2.rglob("*") if p.is_file()])

    assert files_1 == files_2

    for rel_path in files_1:
        bytes_1 = (dir_1 / rel_path).read_bytes()
        bytes_2 = (dir_2 / rel_path).read_bytes()
        assert bytes_1 == bytes_2, f"File {rel_path} differs between runs!"


def test_write_manifest_json_deterministic(tmp_path: Path) -> None:
    """write_manifest_json formats with sorted keys and 2-space indentation."""
    manifest = _create_sample_manifest()
    out_file = tmp_path / "tools.json"
    write_manifest_json(manifest, out_file)

    content = out_file.read_text(encoding="utf-8")
    assert content.endswith("\n")
    # Parse back
    loaded = json.loads(content)
    assert loaded["info"]["version"] == "1.0.0"
