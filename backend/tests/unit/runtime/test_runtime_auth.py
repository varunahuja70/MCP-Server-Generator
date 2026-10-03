"""Tests for runtime authentication."""

import base64

import pytest
import respx

from mcp_forge.templates.server_project.runtime.auth import (
    _OAUTH2_CACHE,
    apply_auth,
    get_oauth2_token,
)


@pytest.mark.asyncio
async def test_apply_auth_api_key_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_API_KEY", "secret_123")
    headers: dict[str, str] = {}
    query: dict[str, str] = {}
    cookies: dict[str, str] = {}

    auth_defs = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "param_name": "X-API-KEY",
            "env_mapping": {"api_key": "MY_API_KEY"},
        }
    }
    reqs: list[dict[str, list[str]]] = [{"ApiKeyAuth": []}]

    await apply_auth(reqs, auth_defs, headers, query, cookies)
    assert headers["X-API-KEY"] == "secret_123"


@pytest.mark.asyncio
async def test_apply_auth_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_TOKEN", "bearer_jwt_xyz")
    headers: dict[str, str] = {}
    query: dict[str, str] = {}
    cookies: dict[str, str] = {}

    auth_defs = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "env_mapping": {"bearer_token": "MY_TOKEN"},
        }
    }
    reqs: list[dict[str, list[str]]] = [{"BearerAuth": []}]

    await apply_auth(reqs, auth_defs, headers, query, cookies)
    assert headers["Authorization"] == "Bearer bearer_jwt_xyz"


@pytest.mark.asyncio
async def test_apply_auth_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASIC_USER", "admin")
    monkeypatch.setenv("BASIC_PASS", "pass123")
    headers: dict[str, str] = {}
    query: dict[str, str] = {}
    cookies: dict[str, str] = {}

    auth_defs = {
        "BasicAuth": {
            "type": "http",
            "scheme": "basic",
            "env_mapping": {"username": "BASIC_USER", "password": "BASIC_PASS"},
        }
    }
    reqs: list[dict[str, list[str]]] = [{"BasicAuth": []}]

    await apply_auth(reqs, auth_defs, headers, query, cookies)
    expected = base64.b64encode(b"admin:pass123").decode()
    assert headers["Authorization"] == f"Basic {expected}"


@pytest.mark.asyncio
async def test_apply_auth_query_and_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("Q_KEY", "query_val")
    monkeypatch.setenv("C_KEY", "cookie_val")
    headers: dict[str, str] = {}
    query: dict[str, str] = {}
    cookies: dict[str, str] = {}

    auth_defs = {
        "QueryAuth": {
            "type": "apiKey",
            "in": "query",
            "param_name": "api_key",
            "env_mapping": {"api_key": "Q_KEY"},
        },
        "CookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "param_name": "session",
            "env_mapping": {"api_key": "C_KEY"},
        },
    }
    await apply_auth([{"QueryAuth": []}, {"CookieAuth": []}], auth_defs, headers, query, cookies)
    assert query["api_key"] == "query_val"


@pytest.mark.asyncio
async def test_apply_auth_missing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    headers: dict[str, str] = {}
    query: dict[str, str] = {}
    cookies: dict[str, str] = {}

    auth_defs = {
        "KeyAuth": {
            "type": "apiKey",
            "in": "header",
            "param_name": "X-Key",
            "env_mapping": {"api_key": "NONEXISTENT"},
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "env_mapping": {"bearer_token": "NONEXISTENT"},
        },
        "BasicAuth": {
            "type": "http",
            "scheme": "basic",
            "env_mapping": {"username": "NONEXISTENT", "password": "PW"},
        },
    }
    # No credentials in env -> should not set headers
    await apply_auth([{"KeyAuth": []}], auth_defs, headers, query, cookies)
    assert "X-Key" not in headers
    await apply_auth([{"BearerAuth": []}], auth_defs, headers, query, cookies)
    assert "Authorization" not in headers
    await apply_auth([{"BasicAuth": []}], auth_defs, headers, query, cookies)
    assert "Authorization" not in headers
    # Empty requirements
    await apply_auth([], auth_defs, headers, query, cookies)


@pytest.mark.asyncio
@respx.mock
async def test_apply_auth_oauth2_in_apply_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLIENT_ID", "cid")
    monkeypatch.setenv("CLIENT_SECRET", "csec")
    monkeypatch.setenv("TOKEN_URL", "https://oauth.example.com/token")

    respx.post("https://oauth.example.com/token").respond(
        json={"access_token": "tok_123", "expires_in": 1800}
    )

    headers: dict[str, str] = {}
    query: dict[str, str] = {}
    cookies: dict[str, str] = {}

    auth_defs = {
        "OAuth": {
            "type": "oauth2",
            "env_mapping": {
                "client_id": "CLIENT_ID",
                "client_secret": "CLIENT_SECRET",
                "token_url": "TOKEN_URL",
            },
        }
    }
    await apply_auth([{"OAuth": []}], auth_defs, headers, query, cookies)
    assert headers["Authorization"] == "Bearer tok_123"


@pytest.mark.asyncio
@respx.mock
async def test_get_oauth2_token() -> None:
    _OAUTH2_CACHE.access_token = None
    _OAUTH2_CACHE.expires_at = 0.0

    token_url = "https://auth.example.com/oauth/token"
    respx.post(token_url).respond(json={"access_token": "token_abc123", "expires_in": 3600})

    token = await get_oauth2_token("client_id", "secret", token_url, client=None)
    assert token == "token_abc123"

    token2 = await get_oauth2_token("client_id", "secret", token_url, client=None)
    assert token2 == "token_abc123"
