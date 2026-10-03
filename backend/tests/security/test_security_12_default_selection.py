"""Security Test 12: Safe default selection.

Requirement from docs/03-security.md Section 11 Test 12:
"12. Default selection test: no write or delete tool is enabled by default for any sample spec."
"""

from pathlib import Path

import pytest

from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping import map_api_to_toolset
from mcp_forge.core.parse import parse_and_validate

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "samples"
SAMPLE_FILES = [
    "bookshop.openapi.yaml",
    "tasks.openapi.json",
    "legacy-swagger2.json",
]


@pytest.mark.parametrize("sample_name", SAMPLE_FILES)
def test_default_selection_no_write_or_delete_enabled(sample_name: str) -> None:
    sample_path = SAMPLES_DIR / sample_name
    text = sample_path.read_text(encoding="utf-8")

    parsed = parse_and_validate(text)
    ir = normalize_spec(parsed)
    toolset = map_api_to_toolset(ir)

    # Verify every enabled tool
    enabled_tools = [t for t in toolset.mapped_tools if t.enabled]

    # Every enabled tool must be GET or HEAD
    for tool in enabled_tools:
        method = tool.manifest_tool.method.upper()
        assert method in ("GET", "HEAD"), (
            f"Write/modify tool '{tool.manifest_tool.name}' ({method}) was enabled by default in {sample_name}!"
        )

    # Verify that all write methods (POST, PUT, PATCH, DELETE) are disabled
    write_tools = [
        t
        for t in toolset.mapped_tools
        if t.manifest_tool.method.upper() in ("POST", "PUT", "PATCH", "DELETE")
    ]
    assert len(write_tools) > 0, f"Expected sample {sample_name} to contain write tools to test."
    for tool in write_tools:
        assert not tool.enabled, (
            f"Write tool '{tool.manifest_tool.name}' ({tool.manifest_tool.method}) must NOT be enabled by default!"
        )
