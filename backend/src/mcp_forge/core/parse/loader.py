"""Safe loading of specification content."""

from typing import Any

from mcp_forge.core.security.safe_yaml import safe_load_yaml
from mcp_forge.errors import InvalidSpecError


def load_spec_dict(
    raw_text: str,
    max_aliases: int = 50,
    max_depth: int = 30,
) -> dict[str, Any]:
    """Parse raw JSON or YAML specification text into a Python dictionary.

    Enforces alias bomb and recursion depth guards.
    """
    if not raw_text or not raw_text.strip():
        raise InvalidSpecError("Specification text is empty.")

    data = safe_load_yaml(
        raw_text,
        max_aliases=max_aliases,
        max_depth=max_depth,
    )

    if not isinstance(data, dict):
        raise InvalidSpecError(
            f"Specification root must be a JSON/YAML mapping/object, got {type(data).__name__}."
        )

    return data
