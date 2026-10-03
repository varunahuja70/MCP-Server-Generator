"""Tests for runtime stderr logging and secret redaction."""

import json

import pytest

from mcp_forge.templates.server_project.runtime.logging import log, redact_secrets


def test_redact_secrets() -> None:
    text = "User bearer token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 and secret sk-1234567890123456789012"
    redacted = redact_secrets(text)
    assert "eyJhbGci" not in redacted
    assert "sk-1234567890123456789012" not in redacted
    assert "[REDACTED]" in redacted


def test_log_writes_to_stderr_never_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    log(
        "INFO",
        "Starting runtime test",
        tool="test_tool",
        details={"key": "sk-1234567890123456789012"},
    )

    captured = capsys.readouterr()
    # CRITICAL: stdout must be completely empty!
    assert captured.out == "", f"stdout must NEVER contain logs, got: '{captured.out}'"

    # stderr must contain structured log with redaction
    assert captured.err != ""
    entry = json.loads(captured.err.strip())
    assert entry["level"] == "INFO"
    assert entry["tool"] == "test_tool"
    assert "Starting runtime test" in entry["message"]
    assert "sk-1234567890123456789012" not in captured.err
