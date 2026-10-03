"""Format detection for JSON and YAML specification text."""

import json
from typing import Literal

import yaml

from mcp_forge.errors import InvalidSpecError


def detect_format(raw_text: str) -> Literal["json", "yaml"]:
    """Detect whether specification text is JSON or YAML.

    Raises InvalidSpecError if neither can be parsed.
    """
    if not raw_text or not raw_text.strip():
        raise InvalidSpecError("Specification text is empty.")

    stripped = raw_text.strip()

    # Fast path: check if starts with JSON object/array delimiters
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            json.loads(stripped)
            return "json"
        except json.JSONDecodeError:
            pass

    # Try YAML safe parsing
    try:
        data = yaml.safe_load(stripped)
        if isinstance(data, (dict, list)):
            return "yaml"
    except yaml.YAMLError as e:
        raise InvalidSpecError(f"Failed to parse specification: {e}") from e

    raise InvalidSpecError(
        "Invalid specification content. Specification must be a valid JSON or YAML document."
    )
