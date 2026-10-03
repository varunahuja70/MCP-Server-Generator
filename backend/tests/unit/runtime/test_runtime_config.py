"""Tests for runtime configuration loading."""

import pytest

from mcp_forge.templates.server_project.runtime.config import RuntimeConfig


def test_runtime_config_defaults() -> None:
    cfg = RuntimeConfig.from_env(default_base_url="https://api.example.com")
    assert cfg.base_url == "https://api.example.com"
    assert cfg.timeout_seconds == 30.0
    assert cfg.max_response_chars == 20000
    assert cfg.allow_private_targets is False
    assert cfg.max_retries == 2
    assert cfg.retry_safe_requests is True


def test_runtime_config_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_BASE_URL", "https://override.example.com")
    monkeypatch.setenv("API_TIMEOUT_SECONDS", "15.5")
    monkeypatch.setenv("MAX_RESPONSE_CHARS", "5000")
    monkeypatch.setenv("ALLOW_PRIVATE_TARGETS", "true")
    monkeypatch.setenv("MAX_RETRIES", "4")
    monkeypatch.setenv("RETRY_SAFE_REQUESTS", "false")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "100.0")

    cfg = RuntimeConfig.from_env()
    assert cfg.base_url == "https://override.example.com"
    assert cfg.timeout_seconds == 15.5
    assert cfg.max_response_chars == 5000
    assert cfg.allow_private_targets is True
    assert cfg.max_retries == 4
    assert cfg.retry_safe_requests is False
    assert cfg.rate_limit_per_minute == 100.0


def test_runtime_config_invalid_env_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_TIMEOUT_SECONDS", "invalid_float")
    monkeypatch.setenv("MAX_RESPONSE_CHARS", "invalid_int")
    monkeypatch.setenv("MAX_RETRIES", "invalid_int")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "invalid_float")

    cfg = RuntimeConfig.from_env()
    assert cfg.timeout_seconds == 30.0
    assert cfg.max_response_chars == 20000
    assert cfg.max_retries == 2
    assert cfg.rate_limit_per_minute == 60.0
