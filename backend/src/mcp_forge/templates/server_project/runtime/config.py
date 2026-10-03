"""Runtime configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass
class RuntimeConfig:
    """Configuration settings for runtime API execution."""

    base_url: str
    timeout_seconds: float = 30.0
    max_response_chars: int = 20000
    allow_private_targets: bool = False
    max_retries: int = 2
    retry_safe_requests: bool = True
    rate_limit_per_minute: float = 60.0

    @classmethod
    def from_env(cls, default_base_url: str = "") -> "RuntimeConfig":
        """Load configuration from environment variables."""
        base_url = os.environ.get("API_BASE_URL", default_base_url).strip()

        timeout_str = os.environ.get("API_TIMEOUT_SECONDS", "30.0")
        try:
            timeout_s = float(timeout_str)
        except ValueError:
            timeout_s = 30.0

        chars_str = os.environ.get("MAX_RESPONSE_CHARS", "20000")
        try:
            max_chars = int(chars_str)
        except ValueError:
            max_chars = 20000

        allow_priv_str = os.environ.get("ALLOW_PRIVATE_TARGETS", "false").lower()
        allow_private = allow_priv_str in ("true", "1", "yes")

        retries_str = os.environ.get("MAX_RETRIES", "2")
        try:
            max_retries = int(retries_str)
        except ValueError:
            max_retries = 2

        retry_safe_str = os.environ.get("RETRY_SAFE_REQUESTS", "true").lower()
        retry_safe = retry_safe_str in ("true", "1", "yes")

        rate_limit_str = os.environ.get("RATE_LIMIT_PER_MINUTE", "60.0")
        try:
            rate_limit = float(rate_limit_str)
        except ValueError:
            rate_limit = 60.0

        return cls(
            base_url=base_url,
            timeout_seconds=timeout_s,
            max_response_chars=max_chars,
            allow_private_targets=allow_private,
            max_retries=max_retries,
            retry_safe_requests=retry_safe,
            rate_limit_per_minute=rate_limit,
        )
