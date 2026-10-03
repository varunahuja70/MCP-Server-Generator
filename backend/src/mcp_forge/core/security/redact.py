"""Centralized secret redaction and credential scrubbing."""

import re
from typing import Any

from mcp_forge.logging_setup import (
    REDACTED_STRING,
    SECRET_PATTERNS,
    SENSITIVE_KEYS,
    get_redacting_filter,
)

# Header scrubbing patterns
AUTH_HEADER_PATTERN = re.compile(
    r"(authorization|proxy-authorization|x-api-key|api-key):\s*([^\r\n]+)",
    re.IGNORECASE,
)


def redact_text(text: str, extra_secrets: set[str] | None = None) -> str:
    """Scrub known tokens, authorization headers, and custom secrets from text."""
    if not text:
        return text

    # Apply global filter secrets
    global_filter = get_redacting_filter()
    all_secrets = set(global_filter.extra_secrets)
    if extra_secrets:
        all_secrets.update(s for s in extra_secrets if s and len(s) >= 4)

    # Redact literal strings
    for secret in all_secrets:
        if secret in text:
            text = text.replace(secret, REDACTED_STRING)

    # Redact authorization header lines
    text = AUTH_HEADER_PATTERN.sub(r"\1: [REDACTED]", text)

    # Redact regex patterns
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(REDACTED_STRING, text)

    return text


def redact_structure(data: Any, extra_secrets: set[str] | None = None) -> Any:
    """Recursively scrub sensitive keys and token patterns from structured dict/list data."""
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            k_str = str(k).lower()
            if k_str in SENSITIVE_KEYS:
                result[k] = REDACTED_STRING
            else:
                result[k] = redact_structure(v, extra_secrets)
        return result
    elif isinstance(data, list):
        return [redact_structure(item, extra_secrets) for item in data]
    elif isinstance(data, tuple):
        return tuple(redact_structure(item, extra_secrets) for item in data)
    elif isinstance(data, str):
        return redact_text(data, extra_secrets)
    return data
