"""Runtime rate limiting with sliding window tracking."""

import time
from collections import defaultdict


class RateLimiter:
    """Sliding-window in-memory rate limiter."""

    def __init__(self, limit_per_minute: float = 60.0) -> None:
        self.limit = limit_per_minute
        self._history: dict[str, list[float]] = defaultdict(list)

    def check_and_record(self, key: str = "global") -> tuple[bool, float]:
        """Check if request is permitted.

        Returns (allowed, retry_after_seconds).
        """
        now = time.time()
        window_start = now - 60.0

        # Purge timestamps older than 60 seconds
        timestamps = [t for t in self._history[key] if t > window_start]
        if timestamps:
            self._history[key] = timestamps
        else:
            self._history.pop(key, None)

        if len(timestamps) >= self.limit:
            oldest = timestamps[0]
            retry_after = max(1.0, 60.0 - (now - oldest))
            return False, retry_after

        if key not in self._history and len(self._history) >= 500:
            # Drop an arbitrary key to prevent memory exhaustion
            old_k = next(iter(self._history))
            self._history.pop(old_k, None)

        self._history.setdefault(key, []).append(now)
        return True, 0.0


# Global runtime limiters
_GLOBAL_LIMITER = RateLimiter(limit_per_minute=120.0)
_TOOL_LIMITERS: dict[str, RateLimiter] = {}
MAX_TOOL_LIMITERS = 500


def check_rate_limit(tool_name: str, tool_limit_per_min: float = 60.0) -> tuple[bool, str]:
    """Check both global and per-tool rate limits.

    Returns (allowed, error_message).
    """
    # 1. Global check
    g_allowed, g_wait = _GLOBAL_LIMITER.check_and_record("global")
    if not g_allowed:
        return False, f"Server rate limit exceeded. Please wait {g_wait:.1f} seconds."

    # 2. Per-tool check with size bounding
    if tool_name not in _TOOL_LIMITERS:
        if len(_TOOL_LIMITERS) >= MAX_TOOL_LIMITERS:
            # Evict oldest entry
            oldest_key = next(iter(_TOOL_LIMITERS))
            _TOOL_LIMITERS.pop(oldest_key, None)
        _TOOL_LIMITERS[tool_name] = RateLimiter(limit_per_minute=tool_limit_per_min)

    t_allowed, t_wait = _TOOL_LIMITERS[tool_name].check_and_record(tool_name)
    if not t_allowed:
        return False, f"Tool '{tool_name}' rate limit exceeded. Please wait {t_wait:.1f} seconds."

    return True, ""
