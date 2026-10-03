"""Internal Representation (IR) and normalization package."""

from typing import Any

from mcp_forge.core.ir.models import (
    IRApi,
    IROperation,
    IRParameter,
    IRRequestBody,
    IRResponse,
    IRSecurityScheme,
    IRServer,
    make_operation_key,
)
from mcp_forge.core.ir.normalize_oas3 import normalize_oas3
from mcp_forge.core.ir.normalize_swagger2 import normalize_swagger2
from mcp_forge.core.ir.schema_tools import (
    cap_schema_size,
    merge_all_of,
    normalize_nullable,
    to_json_schema,
)
from mcp_forge.core.parse import ParsedSpec, detect_spec_kind
from mcp_forge.errors import InvalidSpecError


def normalize_spec(spec: ParsedSpec | dict[str, Any]) -> IRApi:
    """Normalize any parsed specification or dictionary into standard IRApi."""
    if isinstance(spec, ParsedSpec):
        kind = spec.kind
        data = spec.raw_dict
    elif isinstance(spec, dict):
        kind = detect_spec_kind(spec)
        data = spec
    else:
        raise InvalidSpecError(f"Unsupported spec type for normalization: {type(spec).__name__}")

    if kind == "swagger2":
        return normalize_swagger2(data)
    elif kind in ("oas30", "oas31", "oas32"):
        return normalize_oas3(data)
    else:
        raise InvalidSpecError(f"Unsupported specification kind: '{kind}'.")


__all__ = [
    "IRApi",
    "IROperation",
    "IRParameter",
    "IRRequestBody",
    "IRResponse",
    "IRSecurityScheme",
    "IRServer",
    "cap_schema_size",
    "make_operation_key",
    "merge_all_of",
    "normalize_nullable",
    "normalize_oas3",
    "normalize_spec",
    "normalize_swagger2",
    "to_json_schema",
]
