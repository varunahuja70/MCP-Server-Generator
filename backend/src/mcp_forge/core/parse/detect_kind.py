"""Detection of OpenAPI and Swagger specification versions."""

from typing import Any, Literal

from mcp_forge.errors import InvalidSpecError

SpecKind = Literal["swagger2", "oas30", "oas31", "oas32"]


def detect_spec_kind(spec_dict: dict[str, Any]) -> SpecKind:
    """Identify specification standard and version: swagger2, oas30, oas31, oas32."""
    if "swagger" in spec_dict:
        ver = str(spec_dict["swagger"]).strip()
        if ver.startswith("2"):
            return "swagger2"
        raise InvalidSpecError(
            f"Unsupported Swagger version '{ver}'. Only Swagger 2.0 is supported."
        )

    if "openapi" in spec_dict:
        ver = str(spec_dict["openapi"]).strip()
        if ver.startswith("3.0"):
            return "oas30"
        elif ver.startswith("3.1"):
            return "oas31"
        elif ver.startswith("3.2"):
            return "oas32"
        elif ver.startswith("3."):
            return "oas31"
        raise InvalidSpecError(
            f"Unsupported OpenAPI version '{ver}'. Supported versions are 3.0, 3.1, 3.2."
        )

    raise InvalidSpecError(
        "Unrecognized specification standard. Missing 'openapi' or 'swagger' top-level version field."
    )
