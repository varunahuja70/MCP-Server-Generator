"""Tests for runtime ApiClient: retries, SSRF blocking, and execution."""

import httpx
import pytest
import respx

from mcp_forge.templates.server_project.runtime.client import ApiClient, is_private_target
from mcp_forge.templates.server_project.runtime.config import RuntimeConfig


def test_is_private_target() -> None:
    assert is_private_target("http://127.0.0.1:8000/api") is True
    assert is_private_target("http://localhost:8000/api") is True
    assert is_private_target("http://192.168.1.1/api") is True
    assert is_private_target("http://10.0.0.1/api") is True
    assert is_private_target("http://169.254.169.254/latest") is True


@pytest.mark.asyncio
async def test_client_ssrf_blocking() -> None:
    config = RuntimeConfig(base_url="http://127.0.0.1:8000", allow_private_targets=False)
    client = ApiClient(config)

    res = await client.execute_request("GET", "http://127.0.0.1:8000/api/users")
    assert "Blocked access to private network address" in res


@pytest.mark.asyncio
@respx.mock
async def test_client_ssrf_allowed_when_configured() -> None:
    config = RuntimeConfig(base_url="http://127.0.0.1:8000", allow_private_targets=True)
    client = ApiClient(config)

    respx.get("http://127.0.0.1:8000/api/users").respond(json={"users": ["alice"]})

    try:
        res = await client.execute_request("GET", "http://127.0.0.1:8000/api/users")
        assert '"users"' in res
        assert '"alice"' in res
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_client_retries_on_503_and_succeeds() -> None:
    config = RuntimeConfig(
        base_url="https://api.example.com", max_retries=2, retry_safe_requests=True
    )
    client = ApiClient(config)

    route = respx.get("https://api.example.com/data")
    route.side_effect = [
        httpx.Response(503, headers={"retry-after": "0"}),
        httpx.Response(200, json={"status": "ok"}),
    ]

    try:
        res = await client.execute_request("GET", "https://api.example.com/data")
        assert '"status": "ok"' in res
        assert route.call_count == 2
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_client_retries_on_timeout() -> None:
    config = RuntimeConfig(
        base_url="https://api.example.com", max_retries=1, retry_safe_requests=True
    )
    client = ApiClient(config)

    route = respx.get("https://api.example.com/timeout")
    route.side_effect = [
        httpx.ReadTimeout("First attempt timed out"),
        httpx.Response(200, json={"ok": True}),
    ]

    try:
        res = await client.execute_request("GET", "https://api.example.com/timeout")
        assert '"ok": true' in res
        assert route.call_count == 2
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_client_exhausts_retries() -> None:
    config = RuntimeConfig(
        base_url="https://api.example.com", max_retries=1, retry_safe_requests=True
    )
    client = ApiClient(config)

    route = respx.get("https://api.example.com/error")
    route.side_effect = httpx.ConnectError("Connection refused")

    try:
        res = await client.execute_request("GET", "https://api.example.com/error")
        assert "connection" in res.lower()
    finally:
        await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_client_no_retry_for_post() -> None:
    config = RuntimeConfig(
        base_url="https://api.example.com", max_retries=2, retry_safe_requests=True
    )
    client = ApiClient(config)

    route = respx.post("https://api.example.com/data").respond(503)

    try:
        res = await client.execute_request("POST", "https://api.example.com/data")
        assert "HTTP 503" in res
        # Write method must not retry!
        assert route.call_count == 1
    finally:
        await client.close()
