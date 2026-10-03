"""Identifier validation and normalization rules for safe code generation."""

import keyword
import re

IDENTIFIER_REGEX = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

# Disallowed internal runtime or SDK names that would shadow server logic
RESERVED_IDENTIFIERS = {
    *keyword.kwlist,
    "self",
    "cls",
    "mcp",
    "server",
    "runtime",
    "config",
    "client",
    "request",
    "response",
    "tools",
    "tool",
}


def is_valid_identifier(name: str) -> bool:
    """Validate whether name satisfies the identifier security gate: ^[a-z][a-z0-9_]{0,63}$."""
    if not isinstance(name, str):
        return False
    return bool(IDENTIFIER_REGEX.match(name)) and name not in RESERVED_IDENTIFIERS


def sanitize_identifier(raw: str, prefix: str = "tool") -> str:
    """Transform an untrusted input string into a valid, safe identifier.

    Guarantees output matches ^[a-z][a-z0-9_]{0,63}$ and is not a reserved word.
    Never throws; always returns a safe identifier.
    """
    if not raw or not isinstance(raw, str):
        return f"{prefix}_default"

    # Lowercase
    s = raw.lower().strip()

    # Replace hyphens, spaces, slashes, dots with underscores
    s = re.sub(r"[\s\-\./\\]+", "_", s)

    # Replace anything outside [a-z0-9_] with underscore
    s = re.sub(r"[^a-z0-9_]", "_", s)

    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s)

    # Strip leading/trailing underscores
    s = s.strip("_")

    # If empty or starts with a digit, prefix
    if not s or not s[0].isalpha():
        s = f"{prefix}_{s}" if s else f"{prefix}_default"

    # Trim to 64 characters
    s = s[:64].rstrip("_")

    # If it clashes with reserved keyword or runtime identifier, append _op
    if s in RESERVED_IDENTIFIERS:
        s = f"{s[:60]}_op"

    # Final verification against the gate
    if not IDENTIFIER_REGEX.match(s):
        return f"{prefix}_sanitized"

    return s
