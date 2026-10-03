"""Specification parsing and validation package."""

from mcp_forge.core.parse.detect_kind import SpecKind, detect_spec_kind
from mcp_forge.core.parse.loader import load_spec_dict
from mcp_forge.core.parse.parse import ParsedSpec, count_operations, parse_and_validate
from mcp_forge.core.parse.refs import lookup_local_ref, resolve_refs
from mcp_forge.core.parse.validate import validate_spec

__all__ = [
    "ParsedSpec",
    "SpecKind",
    "count_operations",
    "detect_spec_kind",
    "load_spec_dict",
    "lookup_local_ref",
    "parse_and_validate",
    "resolve_refs",
    "validate_spec",
]
