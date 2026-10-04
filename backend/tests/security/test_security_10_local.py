"""Security Test 10 (Local mode parts): Host-header and cross-origin protections."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from mcp_forge.api.app import create_app
from mcp_forge.config import Settings


@pytest.fixture
def app() -> FastAPI:
    settings = Settings(
        forge_mode="local",
        forge_host="127.0.0.1",
        forge_port=8080,
    )
    return create_app(settings)


@pytest.mark.asyncio
async def test_invalid_host_header_rejected(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8080") as client:
        # Malicious Host header attempting DNS rebinding
        response = await client.get("/healthz", headers={"Host": "attacker.com"})
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "INVALID_HOST"


@pytest.mark.asyncio
async def test_valid_host_header_accepted(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8080") as client:
        response = await client.get("/healthz", headers={"Host": "127.0.0.1:8080"})
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        response = await client.get("/healthz", headers={"Host": "localhost"})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_state_change_requires_custom_header(app: FastAPI) -> None:
    # Register a temporary dummy route to test mutation
    @app.post("/test-mutation")
    async def dummy_mutation() -> dict[str, str]:
        return {"result": "success"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8080") as client:
        # POST without X-Forge-Request: 1
        response = await client.post(
            "/test-mutation",
            headers={"Host": "127.0.0.1:8080"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "MISSING_FORGE_HEADER"

        # POST with X-Forge-Request: 1
        response = await client.post(
            "/test-mutation",
            headers={
                "Host": "127.0.0.1:8080",
                "X-Forge-Request": "1",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"result": "success"}


@pytest.mark.asyncio
async def test_state_change_with_untrusted_origin_rejected(app: FastAPI) -> None:
    @app.post("/test-mutation-origin")
    async def dummy_mutation_origin() -> dict[str, str]:
        return {"result": "success"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8080") as client:
        # POST with X-Forge-Request: 1 but foreign attacker Origin
        response = await client.post(
            "/test-mutation-origin",
            headers={
                "Host": "127.0.0.1:8080",
                "X-Forge-Request": "1",
                "Origin": "http://evil.corp",
            },
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "INVALID_ORIGIN"


@pytest.mark.asyncio
async def test_security_headers_present(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8080") as client:
        response = await client.get("/healthz", headers={"Host": "127.0.0.1:8080"})
        assert response.status_code == 200
        headers = response.headers
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["x-frame-options"] == "DENY"
        assert headers["referrer-policy"] == "same-origin"
        assert "default-src 'self'" in headers["content-security-policy"]


@pytest.mark.asyncio
async def test_ipv6_host_header_handling(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://[::1]:8080") as client:
        # Bracketed IPv6 with port
        response = await client.get("/healthz", headers={"Host": "[::1]:8080"})
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Bracketed IPv6 without port
        response = await client.get("/healthz", headers={"Host": "[::1]"})
        assert response.status_code == 200

        # Bare IPv6 without port
        response = await client.get("/healthz", headers={"Host": "::1"})
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_ipv6_origin_handling(app: FastAPI) -> None:
    @app.post("/test-mutation-ipv6")
    async def dummy_mutation() -> dict[str, str]:
        return {"result": "success"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://[::1]:8080") as client:
        # Valid IPv6 Origin with port
        response = await client.post(
            "/test-mutation-ipv6",
            headers={
                "Host": "[::1]:8080",
                "X-Forge-Request": "1",
                "Origin": "http://[::1]:8080",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"result": "success"}
