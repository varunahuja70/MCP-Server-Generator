"""Tool mapping package."""

from mcp_forge.core.mapping.annotations import get_tool_annotations
from mcp_forge.core.mapping.auth import map_all_security_schemes, map_security_scheme_to_env
from mcp_forge.core.mapping.descriptions import build_tool_description, clean_description
from mcp_forge.core.mapping.input_schema import build_input_schema
from mcp_forge.core.mapping.manifest import (
    TOOLS_JSON_SCHEMA,
    ManifestDoc,
    ManifestInfo,
    ManifestTool,
    MappedTool,
    ToolSet,
    validate_manifest,
)
from mcp_forge.core.mapping.mapper import map_api_to_toolset
from mcp_forge.core.mapping.names import resolve_tool_name, sanitize_tool_name
from mcp_forge.core.mapping.selection import (
    apply_preset,
    determine_default_selection,
    is_read_only_method,
)

__all__ = [
    "TOOLS_JSON_SCHEMA",
    "ManifestDoc",
    "ManifestInfo",
    "ManifestTool",
    "MappedTool",
    "ToolSet",
    "apply_preset",
    "build_input_schema",
    "build_tool_description",
    "clean_description",
    "determine_default_selection",
    "get_tool_annotations",
    "is_read_only_method",
    "map_all_security_schemes",
    "map_api_to_toolset",
    "map_security_scheme_to_env",
    "resolve_tool_name",
    "sanitize_tool_name",
    "validate_manifest",
]
