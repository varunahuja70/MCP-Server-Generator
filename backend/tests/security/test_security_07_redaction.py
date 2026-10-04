"""Security Test 7 (Redaction unit tests part)."""

from mcp_forge.core.security.redact import redact_structure, redact_text


def test_redact_bearer_tokens_and_keys() -> None:
    text = (
        "Authorization: Bearer sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890\n"
        "User GitHub key: ghp_1234567890abcdefghijklmnopqrstuvwxyz\n"
        "AWS credential AKIAIOSFODNN7EXAMPLE used."
    )
    result = redact_text(text)
    assert "sk-ant-api03" not in result
    assert "ghp_1234567890" not in result
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    assert "[REDACTED]" in result


def test_redact_custom_secret() -> None:
    custom_secret = "my_custom_secret_api_key_44332211"
    text = f"Calling provider with token {custom_secret} on host"
    result = redact_text(text, extra_secrets={custom_secret})
    assert custom_secret not in result
    assert "[REDACTED]" in result


def test_redact_nested_dictionary_and_lists() -> None:
    payload = {
        "user": "alice",
        "authorization": "Bearer token123",
        "nested": {
            "password": "secretpassword",
            "safe_field": 12345,
            "items": [
                {"token": "xyz987"},
                {"text": "Using key sk-123456789012345678901234"},
            ],
        },
    }
    redacted = redact_structure(payload)
    assert redacted["user"] == "alice"
    assert redacted["authorization"] == "[REDACTED]"
    assert redacted["nested"]["password"] == "[REDACTED]"
    assert redacted["nested"]["safe_field"] == 12345
    assert redacted["nested"]["items"][0]["token"] == "[REDACTED]"
    assert "sk-" not in redacted["nested"]["items"][1]["text"]
    assert "[REDACTED]" in redacted["nested"]["items"][1]["text"]


def test_trace_recorder_redacts_credentials() -> None:
    """TraceRecorder scrubs secrets and credentials from trace events."""
    from mcp_forge.playground.trace import TraceRecorder

    user_secret = "super_secret_api_token_9999"
    recorder = TraceRecorder(session_id="test-session", extra_secrets={user_secret})

    event = recorder.record(
        direction="client_to_server",
        message={
            "method": "tools/call",
            "params": {
                "name": "get_data",
                "arguments": {"token": user_secret, "auth": "Bearer secret_12345"},
            },
        },
    )

    assert user_secret not in event["message_json"]
    assert "[REDACTED]" in event["message_json"]
