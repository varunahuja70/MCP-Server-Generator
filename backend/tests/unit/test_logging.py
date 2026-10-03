"""Unit tests for structlog redaction filter and sensitive data scrubbing."""

from mcp_forge.logging_setup import (
    RedactingFilter,
    register_secret_for_redaction,
)


def test_redact_sensitive_keys() -> None:
    rf = RedactingFilter()
    data = {
        "user": "developer",
        "authorization": "Bearer secret123",
        "password": "mypassword",
        "nested": {
            "token": "sensitive-nested-token",
            "normal": "regular_value",
        },
    }
    redacted = rf.redact_value(None, data)
    assert redacted["authorization"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["nested"]["token"] == "[REDACTED]"
    assert redacted["nested"]["normal"] == "regular_value"
    assert redacted["user"] == "developer"


def test_redact_secret_patterns_in_text() -> None:
    rf = RedactingFilter()

    # Bearer token
    assert rf.redact_text("Sending request with Bearer eyJhbGciOiJIUzI1NiJ9.abc.def") == (
        "Sending request with [REDACTED]"
    )

    # OpenAI key pattern
    assert rf.redact_text("Key sk-123456789012345678901234 was used") == ("Key [REDACTED] was used")

    # GitHub PAT pattern
    assert rf.redact_text("Connecting with ghp_123456789012345678901234") == (
        "Connecting with [REDACTED]"
    )

    # AWS access key pattern
    assert rf.redact_text("AWS key AKIAIOSFODNN7EXAMPLE") == ("AWS key [REDACTED]")


def test_custom_registered_secret_is_redacted() -> None:
    secret = "session_live_super_secret_998877"
    register_secret_for_redaction(secret)
    from mcp_forge.logging_setup import get_redacting_filter

    filter_inst = get_redacting_filter()
    text = f"API error occurred while connecting with {secret} on endpoint"
    assert secret not in filter_inst.redact_text(text)
    assert "[REDACTED]" in filter_inst.redact_text(text)
