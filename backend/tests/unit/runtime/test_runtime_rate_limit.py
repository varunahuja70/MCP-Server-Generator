"""Tests for runtime rate limiting."""

from mcp_forge.templates.server_project.runtime.rate_limit import RateLimiter, check_rate_limit


def test_sliding_window_rate_limiter() -> None:
    limiter = RateLimiter(limit_per_minute=3)

    # 3 requests succeed
    allowed1, _ = limiter.check_and_record("test_key")
    allowed2, _ = limiter.check_and_record("test_key")
    allowed3, _ = limiter.check_and_record("test_key")
    assert allowed1 and allowed2 and allowed3

    # 4th request blocked
    allowed4, wait = limiter.check_and_record("test_key")
    assert not allowed4
    assert wait > 0


def test_check_rate_limit_function() -> None:
    allowed, err = check_rate_limit("tool_abc", tool_limit_per_min=50)
    assert allowed is True
    assert err == ""

    # Exhaust tool rate limit
    for _ in range(50):
        check_rate_limit("tool_exhaust", tool_limit_per_min=1)
    allowed_blocked, err_blocked = check_rate_limit("tool_exhaust", tool_limit_per_min=1)
    assert allowed_blocked is False
    assert "rate limit exceeded" in err_blocked
