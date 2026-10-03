"""Unit tests for configuration and security validation rules."""

import pytest

from mcp_forge.config import Settings
from mcp_forge.errors import UnsafeConfigError


def test_default_local_config_is_safe() -> None:
    settings = Settings(
        forge_mode="local",
        forge_host="127.0.0.1",
        forge_port=8080,
    )
    assert settings.forge_mode == "local"
    assert settings.forge_host == "127.0.0.1"
    assert settings.playground_enabled is True
    assert "sqlite+aiosqlite:///" in str(settings.database_url)


def test_exposed_mode_refuses_without_token() -> None:
    with pytest.raises(UnsafeConfigError, match="requires FORGE_ACCESS_TOKEN"):
        Settings(
            forge_mode="exposed",
            forge_host="0.0.0.0",
            forge_access_token=None,
        )


def test_exposed_mode_refuses_short_token() -> None:
    with pytest.raises(UnsafeConfigError, match="at least 16 characters"):
        Settings(
            forge_mode="exposed",
            forge_host="0.0.0.0",
            forge_access_token="too-short",
        )


def test_exposed_mode_accepts_valid_token() -> None:
    token = "a" * 32
    settings = Settings(
        forge_mode="exposed",
        forge_host="0.0.0.0",
        forge_access_token=token,
    )
    assert settings.forge_mode == "exposed"
    assert settings.forge_access_token == token
    assert settings.playground_enabled is False  # Playground disabled by default in exposed mode


def test_local_mode_refuses_non_loopback_host() -> None:
    with pytest.raises(UnsafeConfigError, match="Binding to non-loopback host"):
        Settings(
            forge_mode="local",
            forge_host="0.0.0.0",
        )

    with pytest.raises(UnsafeConfigError, match="Binding to non-loopback host"):
        Settings(
            forge_mode="local",
            forge_host="192.168.1.50",
        )
