"""Tool naming rules, sanitization, and collision resolution."""

import keyword
import re

from mcp_forge.core.security.identifiers import is_valid_identifier, sanitize_identifier

RESERVED_NAMES = {
    *keyword.kwlist,
    "server",
    "client",
    "tool",
    "tools",
    "main",
    "runtime",
    "config",
    "json",
    "sys",
    "os",
    "run",
    "handle",
    "request",
    "response",
    "auth",
}


def _path_to_words(path: str) -> list[str]:
    """Convert URL path into clean word tokens, stripping parameters and slashes."""
    # e.g. "/books/{book_id}/reviews" -> ["books", "by", "book", "id", "reviews"]
    parts: list[str] = []
    for segment in path.strip("/").split("/"):
        if not segment:
            continue
        if segment.startswith("{") and segment.endswith("}"):
            param = segment[1:-1]
            parts.extend(["by", param])
        else:
            parts.append(segment)
    return parts


def derive_raw_name(method: str, path: str, operation_id: str | None = None) -> str:
    """Derive raw candidate name from operationId or method + path."""
    if operation_id and operation_id.strip():
        # Convert camelCase or PascalCase or kebab-case to snake_case
        s = operation_id.strip()
        # insert underscore before caps: fooBar -> foo_Bar
        s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
        # convert kebab or dots or spaces to underscores
        s = re.sub(r"[\s\.\-]+", "_", s)
        return s.lower()

    words = [method.lower()] + _path_to_words(path)
    combined = "_".join(words)
    return combined.lower()


def sanitize_tool_name(raw_name: str, prefix: str | None = None) -> str:
    """Sanitize name to match ^[a-z][a-z0-9_]{0,63}$."""
    name = sanitize_identifier(raw_name, prefix="op_")

    if prefix and prefix.strip():
        clean_prefix = sanitize_identifier(prefix.strip(), prefix="pfx_")
        name = f"{clean_prefix}_{name}"

    if name in RESERVED_NAMES:
        name = f"{name}_tool"

    # Enforce maximum 64 characters
    if len(name) > 64:
        name = name[:64].rstrip("_")

    # Final check: if for any reason it's invalid, fallback to safe name
    if not is_valid_identifier(name):
        name = sanitize_identifier(f"op_{name}", prefix="op_")[:64].rstrip("_")

    return name


def resolve_tool_name(
    method: str,
    path: str,
    operation_id: str | None = None,
    prefix: str | None = None,
    existing_names: set[str] | None = None,
) -> tuple[str, bool]:
    """Generate a unique, valid tool name.

    Returns (resolved_name, had_collision).
    """
    raw = derive_raw_name(method, path, operation_id)
    base_name = sanitize_tool_name(raw, prefix=prefix)
    had_collision = False

    if existing_names is None or base_name not in existing_names:
        return base_name, False

    # Disambiguate collision
    had_collision = True
    suffix = 2
    while True:
        candidate_suffix = f"_{suffix}"
        max_base_len = 64 - len(candidate_suffix)
        candidate = f"{base_name[:max_base_len].rstrip('_')}{candidate_suffix}"
        if candidate not in existing_names and is_valid_identifier(candidate):
            return candidate, had_collision
        suffix += 1
