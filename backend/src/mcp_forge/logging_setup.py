"""Structured JSON logging with sensitive data redaction."""

import logging
import re
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

# Standard sensitive key names (case-insensitive)
SENSITIVE_KEYS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "password",
    "forge_access_token",
    "client_secret",
}

# Regex patterns for high-entropy secrets and standard tokens
SECRET_PATTERNS = [
    re.compile(r"Bearer\s+([A-Za-z0-9_\-\.]+)", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),  # OpenAI style
    re.compile(r"ghp_[A-Za-z0-9]{20,}", re.IGNORECASE),  # GitHub personal token
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),  # AWS access key
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]+"),  # JWT
]

REDACTED_STRING = "[REDACTED]"


class RedactingFilter:
    """Filter that traverses data structures and redacts secrets."""

    def __init__(self, extra_secrets: set[str] | None = None) -> None:
        self.extra_secrets = {s for s in (extra_secrets or set()) if s and len(s) >= 4}

    def redact_text(self, text: str) -> str:
        """Mask known patterns and custom secret strings in a text string."""
        if not text:
            return text

        # Redact known extra secrets
        for secret in self.extra_secrets:
            if secret in text:
                text = text.replace(secret, REDACTED_STRING)

        # Redact regex patterns
        for pattern in SECRET_PATTERNS:
            text = pattern.sub(REDACTED_STRING, text)

        return text

    def redact_value(self, key: str | None, value: Any) -> Any:
        """Recursively redact dictionary and list structures."""
        if key and key.lower() in SENSITIVE_KEYS:
            return REDACTED_STRING

        if isinstance(value, str):
            return self.redact_text(value)
        elif isinstance(value, dict):
            return {k: self.redact_value(str(k), v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.redact_value(key, item) for item in value]
        elif isinstance(value, tuple):
            return tuple(self.redact_value(key, item) for item in value)

        return value

    def __call__(
        self,
        logger: Any,
        method_name: str,
        event_dict: MutableMapping[str, Any],
    ) -> MutableMapping[str, Any]:
        """Structlog processor entrypoint."""
        for k, v in list(event_dict.items()):
            event_dict[k] = self.redact_value(k, v)
        return event_dict


_redacting_filter = RedactingFilter()


def register_secret_for_redaction(secret: str) -> None:
    """Register a runtime credential to be scrubbed from logs and traces."""
    if secret and len(secret) >= 4:
        _redacting_filter.extra_secrets.add(secret)


def get_redacting_filter() -> RedactingFilter:
    return _redacting_filter


def setup_logging(log_level: str = "INFO", stderr_only: bool = False) -> None:
    """Configure structlog with JSON output and secret redaction."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    target_stream = sys.stderr if stderr_only else sys.stdout

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redacting_filter,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(target_stream),
        cache_logger_on_first_use=True,
    )
