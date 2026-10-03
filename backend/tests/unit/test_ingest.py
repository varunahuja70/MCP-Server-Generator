"""Unit tests for specification ingestion (upload, text, URL)."""

import socket
from typing import Any

import pytest
import respx
from httpx import Response

from mcp_forge.core.ingest.sources import (
    ingest_from_bytes,
    ingest_from_text,
    ingest_from_url,
)
from mcp_forge.errors import InvalidSpecError, SSRFBlockedError


@pytest.fixture(autouse=True)
def mock_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock DNS resolution for test hostnames."""
    original_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(host: Any, port: Any, *args: Any, **kwargs: Any) -> Any:
        if host in ("specs.example.com", "slow.example.com", "redirect.example.com"):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port or 0))]
        return original_getaddrinfo(host, port, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


def test_ingest_from_text_json_and_yaml() -> None:
    json_text = '{"openapi": "3.0.0", "info": {"title": "Test"}}'
    res_json = ingest_from_text(json_text, source_type="paste")
    assert res_json.format == "json"
    assert res_json.source_type == "paste"
    assert res_json.byte_count == len(json_text.encode("utf-8"))
    assert res_json.has_stripped_chars is False

    yaml_text = "openapi: 3.0.0\ninfo:\n  title: Test\n"
    res_yaml = ingest_from_text(yaml_text, source_type="sample")
    assert res_yaml.format == "yaml"
    assert res_yaml.source_type == "sample"


def test_ingest_from_text_strips_unicode() -> None:
    hostile_text = '{"openapi": "3.0.0",\u200b "info": {"title": "Test\ufeff"}}'
    res = ingest_from_text(hostile_text)
    assert res.has_stripped_chars is True
    assert res.stripped_char_count == 2
    assert "\u200b" not in res.raw_text
    assert "\ufeff" not in res.raw_text


def test_ingest_from_text_oversize() -> None:
    large_text = "a" * 1000
    with pytest.raises(InvalidSpecError, match="exceeds maximum limit"):
        ingest_from_text(large_text, max_bytes=500)


def test_ingest_from_bytes_with_bom() -> None:
    yaml_bytes_with_bom = b"\xef\xbb\xbfopenapi: 3.0.0\ninfo:\n  title: Test\n"
    res = ingest_from_bytes(yaml_bytes_with_bom, source_ref="test.yaml")
    assert res.format == "yaml"
    assert res.source_ref == "test.yaml"
    assert "openapi: 3.0.0" in res.raw_text


def test_ingest_from_bytes_invalid_encoding() -> None:
    invalid_bytes = b"\xff\xfe\x00\x00not_utf8"
    with pytest.raises(InvalidSpecError, match="encoding error"):
        ingest_from_bytes(invalid_bytes)


@pytest.mark.asyncio
@respx.mock
async def test_ingest_from_url_valid() -> None:
    respx.get("https://specs.example.com/openapi.json").mock(
        return_value=Response(
            200,
            content=b'{"openapi": "3.0.0", "info": {"title": "Remote API"}}',
            headers={"Content-Type": "application/json"},
        )
    )
    res = await ingest_from_url("https://specs.example.com/openapi.json")
    assert res.format == "json"
    assert "Remote API" in res.raw_text
    assert res.source_type == "url"


@pytest.mark.asyncio
@respx.mock
async def test_ingest_from_url_wrong_content_type() -> None:
    respx.get("https://specs.example.com/not-a-spec.png").mock(
        return_value=Response(
            200,
            content=b"\x89PNG\r\n\x1a\nfakeimage",
            headers={"Content-Type": "image/png"},
        )
    )
    with pytest.raises(InvalidSpecError, match="Invalid Content-Type"):
        await ingest_from_url("https://specs.example.com/not-a-spec.png")


@pytest.mark.asyncio
@respx.mock
async def test_ingest_from_url_redirect_to_private() -> None:
    respx.get("https://redirect.example.com/spec.yaml").mock(
        return_value=Response(
            302,
            headers={"Location": "http://10.0.0.1/private.yaml"},
        )
    )
    with pytest.raises(SSRFBlockedError):
        await ingest_from_url("https://redirect.example.com/spec.yaml")
