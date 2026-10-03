"""Main parsing orchestrator combining loading, detection, validation, and ref resolution."""

from dataclasses import dataclass
from typing import Any

from mcp_forge.core.parse.detect_kind import SpecKind, detect_spec_kind
from mcp_forge.core.parse.loader import load_spec_dict
from mcp_forge.core.parse.refs import resolve_refs
from mcp_forge.core.parse.validate import validate_spec

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}


def count_operations(spec_dict: dict[str, Any]) -> int:
    """Count the total number of operations across all paths."""
    paths = spec_dict.get("paths")
    if not isinstance(paths, dict):
        return 0

    count = 0
    for _path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for key in path_item:
            if key.lower() in HTTP_METHODS:
                count += 1
    return count


@dataclass(frozen=True)
class ParsedSpec:
    """Result of parsing and validating an OpenAPI / Swagger specification."""

    kind: SpecKind
    raw_dict: dict[str, Any]
    resolved_dict: dict[str, Any]
    title: str
    version: str
    description: str
    operation_count: int


def parse_and_validate(
    raw_text: str,
    validate: bool = True,
    allow_remote_refs: bool = False,
    max_ref_depth: int = 15,
) -> ParsedSpec:
    """Parse raw text, detect specification kind, validate against official schema, and resolve local references."""
    spec_dict = load_spec_dict(raw_text)
    kind = detect_spec_kind(spec_dict)

    if validate:
        validate_spec(spec_dict, kind)

    # Resolve local references with cycle protection
    resolved = resolve_refs(
        spec_dict,
        root=spec_dict,
        allow_remote=allow_remote_refs,
        max_depth=max_ref_depth,
    )

    info = spec_dict.get("info")
    title = "Untitled API"
    version = "1.0.0"
    description = ""
    if isinstance(info, dict):
        title = str(info.get("title", "Untitled API"))
        version = str(info.get("version", "1.0.0"))
        description = str(info.get("description", ""))

    op_count = count_operations(spec_dict)

    return ParsedSpec(
        kind=kind,
        raw_dict=spec_dict,
        resolved_dict=resolved,
        title=title,
        version=version,
        description=description,
        operation_count=op_count,
    )
