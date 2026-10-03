"""OpenAPI and Swagger specification schema validation."""

from typing import Any

from openapi_spec_validator import (
    OpenAPIV2SpecValidator,
    OpenAPIV30SpecValidator,
    OpenAPIV31SpecValidator,
    OpenAPIV32SpecValidator,
)

from mcp_forge.core.parse.detect_kind import SpecKind
from mcp_forge.errors import InvalidSpecError

VALIDATOR_CLASSES = {
    "swagger2": OpenAPIV2SpecValidator,
    "oas30": OpenAPIV30SpecValidator,
    "oas31": OpenAPIV31SpecValidator,
    "oas32": OpenAPIV32SpecValidator,
}


def validate_spec(spec_dict: dict[str, Any], spec_kind: SpecKind) -> None:
    """Validate specification structure against the official schema standard.

    Raises InvalidSpecError with detailed error list and JSON pointers if invalid.
    """
    validator_cls = VALIDATOR_CLASSES.get(spec_kind)
    if not validator_cls:
        raise InvalidSpecError(
            f"No schema validator available for specification kind '{spec_kind}'."
        )

    validator = validator_cls(spec_dict)
    errors = list(validator.iter_errors())
    if not errors:
        return

    formatted_errors = []
    for err in errors:
        ptr = "/" + "/".join(str(p) for p in err.path) if err.path else "/"
        formatted_errors.append(
            {
                "path": ptr,
                "message": err.message,
                "validator": getattr(err, "validator", "schema"),
            }
        )

    # Primary error message highlights the first finding
    primary_msg = (
        f"Validation failed at '{formatted_errors[0]['path']}': {formatted_errors[0]['message']}"
    )
    raise InvalidSpecError(
        primary_msg,
        details={"errors": formatted_errors, "error_count": len(formatted_errors)},
    )
