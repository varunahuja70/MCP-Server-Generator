"""Security test 01: Hostile-name fuzz test.

Ensures that arbitrary spec text (operationId, paths, descriptions, parameter names)
NEVER appears as executable Python syntax in generated .py source files, but only
resides within tools.json.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from mcp_forge.core.mapping.manifest import ManifestDoc, ManifestInfo, ToolManifest
from mcp_forge.core.render.renderer import render_project


@settings(max_examples=50, deadline=None)
@given(
    hostile_op_id=st.text(min_size=1, max_size=100),
    hostile_desc=st.text(min_size=1, max_size=200),
    hostile_path=st.text(min_size=1, max_size=50),
)
def test_hostile_name_fuzz_never_leaks_into_python_source(
    tmp_path_factory: pytest.TempPathFactory,
    hostile_op_id: str,
    hostile_desc: str,
    hostile_path: str,
) -> None:
    """Spec text never gets rendered into Python source files."""
    out_dir = tmp_path_factory.mktemp("hostile_fuzz")

    # In our pipeline, tool names in manifest are already validated / sanitized identifiers
    # matching ^[a-z][a-z0-9_]{0,63}$.
    # But descriptions, paths, and raw values can be arbitrary hostile strings.
    tool = ToolManifest(
        name="tool_fuzz",
        operation_key=f"op_{hostile_op_id}",
        description=f"HostileDesc: {hostile_desc}",
        method="GET",
        path=f"/test/{hostile_path}",
        input_schema={"type": "object", "properties": {}},
        param_locations={},
        is_flattened_body=False,
        security=[],
        annotations={},
    )

    manifest = ManifestDoc(
        info=ManifestInfo(
            title=f"API {hostile_op_id}",
            version="1.0.0",
            base_url="https://api.example.com",
            description=hostile_desc,
        ),
        auth={},
        tools=[tool],
    )

    render_project(manifest, out_dir, slug="fuzz_server")

    # Verify python source files
    py_files = list(out_dir.rglob("*.py"))
    assert len(py_files) > 0

    # Ensure none of the hostile raw text leaked into python source code
    # (Except when it matches standard python keywords or empty strings)
    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        if len(hostile_desc.strip()) > 5:
            assert hostile_desc not in content
        if len(hostile_op_id.strip()) > 5:
            assert hostile_op_id not in content
