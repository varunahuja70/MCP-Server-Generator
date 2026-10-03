"""Security Test 5: SSRF matrix for spec links, redirects, and IP representations."""

import socket
from typing import Any

import pytest
import respx
from httpx import Response

from mcp_forge.core.security.ssrf import (
    safe_fetch_url,
    validate_url_ssrf,
)
from mcp_forge.errors import SSRFBlockedError


@pytest.fixture(autouse=True)
def mock_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock DNS resolution for fake test hostnames to public IP."""
    original_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(host: Any, port: Any, *args: Any, **kwargs: Any) -> Any:
        if host in ("public-api.com", "api.example.com"):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 0))]
        return original_getaddrinfo(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


def test_ssrf_blocks_private_and_loopback_ranges() -> None:
    blocked_urls = [
        "http://127.0.0.1/spec.yaml",
        "http://127.0.0.2:8000/spec.yaml",
        "http://localhost/spec.yaml",
        "http://[::1]/spec.yaml",
        "http://10.0.0.1/spec.json",
        "http://10.255.255.254/spec.json",
        "http://172.16.0.1/spec.yaml",
        "http://172.31.255.254/spec.yaml",
        "http://192.168.1.1/spec.yaml",
        "http://169.254.169.254/latest/meta-data",  # Cloud metadata
        "http://0.0.0.0/spec.yaml",
        "http://255.255.255.255/spec.yaml",
        "http://[fe80::1]/spec.yaml",  # IPv6 link-local
        "http://[fc00::1]/spec.yaml",  # IPv6 unique-local
    ]
    for url in blocked_urls:
        with pytest.raises(SSRFBlockedError):
            validate_url_ssrf(url)


def test_ssrf_blocks_numeric_hex_octal_ip_representations() -> None:
    blocked_representations = [
        "http://2130706433/",  # Decimal 127.0.0.1
        "http://0x7f000001/",  # Hex 127.0.0.1
        "http://0177.0.0.1/",  # Octal 127.0.0.1
        "http://2886729729/",  # Decimal 172.16.0.1
        "http://0xa000001/",  # Hex 10.0.0.1
        "http://0251.0254.0252.0376/",  # Octal 169.254.169.254
    ]
    for url in blocked_representations:
        with pytest.raises(SSRFBlockedError):
            validate_url_ssrf(url)


def test_ssrf_rejects_embedded_credentials() -> None:
    credential_urls = [
        "http://user:password@example.com/spec.yaml",
        "https://admin:secret@api.github.com/spec.json",
        "http://token:@example.com/spec.yaml",
    ]
    for url in credential_urls:
        with pytest.raises(SSRFBlockedError, match="embedded authentication credentials"):
            validate_url_ssrf(url)


def test_ssrf_rejects_unsupported_schemes() -> None:
    bad_schemes = [
        "ftp://example.com/spec.yaml",
        "file:///etc/passwd",
        "gopher://example.com/",
        "data:text/plain;base64,SGVsbG8=",
    ]
    for url in bad_schemes:
        with pytest.raises(SSRFBlockedError, match="Unsupported URL scheme"):
            validate_url_ssrf(url)


@pytest.mark.asyncio
@respx.mock
async def test_redirect_to_private_ip_is_blocked_on_hop() -> None:
    # Initial public URL redirects to private cloud metadata service
    respx.get("https://public-api.com/spec.yaml").mock(
        return_value=Response(
            status_code=302,
            headers={"Location": "http://169.254.169.254/latest/meta-data"},
        )
    )

    with pytest.raises(SSRFBlockedError):
        await safe_fetch_url("https://public-api.com/spec.yaml")


@pytest.mark.asyncio
@respx.mock
async def test_excessive_redirects_rejected() -> None:
    # Redirect loop
    respx.get("https://public-api.com/step1").mock(
        return_value=Response(302, headers={"Location": "https://public-api.com/step2"})
    )
    respx.get("https://public-api.com/step2").mock(
        return_value=Response(302, headers={"Location": "https://public-api.com/step3"})
    )
    respx.get("https://public-api.com/step3").mock(
        return_value=Response(302, headers={"Location": "https://public-api.com/step4"})
    )
    respx.get("https://public-api.com/step4").mock(
        return_value=Response(302, headers={"Location": "https://public-api.com/step5"})
    )

    with pytest.raises(SSRFBlockedError, match="Maximum redirects"):
        await safe_fetch_url("https://public-api.com/step1", max_redirects=3)


@pytest.mark.asyncio
@respx.mock
async def test_safe_fetch_public_url_succeeds() -> None:
    content = b"openapi: 3.0.0\ninfo:\n  title: Sample\n"
    respx.get("https://api.example.com/openapi.yaml").mock(
        return_value=Response(
            200,
            content=content,
            headers={"Content-Type": "application/yaml"},
        )
    )

    data, content_type = await safe_fetch_url("https://api.example.com/openapi.yaml")
    assert data == content
    assert "yaml" in content_type
