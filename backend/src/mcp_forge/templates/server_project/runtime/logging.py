"""Runtime logging strictly to stderr with secret redaction."""

import json
import re
import sys
import time
from typing import Any

# Standard credential patterns to redact from logs
SECRET_PATTERNS = [
    re.compile(r"Bearer\s+([a-zA-Z0-9_\-\.]{10,})", re.IGNORECASE),
    re.compile(r"Basic\s+([a-zA-Z0-9+/=]{10,})", re.IGNORECASE),
    re.compile(r"(sk-[a-zA-Z0-9_\-]{20,})"),
    re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{50,})"),
    re.compile(r"(AKIA[0-9A-Z]{16})"),
    re.compile(r'(["\']?(?:api[_-]?key|password|secret|token)["\']?\s*[:=]\s*["\'])([^"\']+)'),
]


def redact_secrets(text: str) -> str:
    """Scrub sensitive credentials from a log string."""
    if not text:
        return text

    scrubbed = text
    for pat in SECRET_PATTERNS:
        if pat.groups == 2:
            scrubbed = pat.sub(r"\1[REDACTED]", scrubbed)
        elif pat.groups == 1:
            scrubbed = pat.sub(r"[REDACTED]", scrubbed)

    return scrubbed


def log(
    level: str,
    message: str,
    tool: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    """Log structured message to sys.stderr ONLY (stdout is strictly reserved for MCP JSON-RPC)."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": level.upper(),
        "message": redact_secrets(message),
    }
    if tool:
        entry["tool"] = tool
    if details:
        safe_details = {k: redact_secrets(str(v)) for k, v in details.items()}
        entry["details"] = safe_details  # type: ignore[assignment]

    log_line = json.dumps(entry) + "\n"
    # Write to stderr explicitly
    sys.stderr.write(log_line)
    sys.stderr.flush()
