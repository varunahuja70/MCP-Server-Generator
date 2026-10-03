"""Tests for runtime response shaping and error formatting."""

import httpx

from mcp_forge.templates.server_project.runtime.response import (
    shape_error_response,
    shape_exception_error,
    shape_success_response,
)


def test_shape_success_response_json() -> None:
    resp = httpx.Response(
        status_code=200,
        content=b'{"id":"1","title":"Clean Code"}',
        headers={"content-type": "application/json"},
    )
    shaped = shape_success_response(resp)
    assert '"title": "Clean Code"' in shaped


def test_shape_success_response_truncation() -> None:
    large_payload = "x" * 1000
    resp = httpx.Response(
        status_code=200, text=large_payload, headers={"content-type": "text/plain"}
    )
    shaped = shape_success_response(resp, max_chars=100)
    assert len(shaped) < 1000
    assert (
        "[Truncated: response exceeded limit of 100 characters (original length: 1000 characters)]"
        in shaped
    )


def test_shape_success_response_non_json() -> None:
    resp = httpx.Response(
        status_code=200, text="Plain text", headers={"content-type": "application/json"}
    )
    shaped = shape_success_response(resp)
    assert shaped == "Plain text"


def test_shape_error_response_hints() -> None:
    resp_404 = httpx.Response(status_code=404, text="Not Found")
    assert "Resource not found" in shape_error_response(resp_404)

    resp_401 = httpx.Response(
        status_code=401, text="Unauthorized: token sk-1234567890123456789012 invalid"
    )
    shaped_401 = shape_error_response(resp_401)
    assert "Authentication failed" in shaped_401
    assert "sk-1234567890123456789012" not in shaped_401
    assert "[REDACTED]" in shaped_401

    resp_422 = httpx.Response(status_code=422, text="Unprocessable Entity")
    assert "Invalid request payload" in shape_error_response(resp_422)

    resp_500 = httpx.Response(status_code=500, text="Internal Server Error")
    assert "internal error" in shape_error_response(resp_500).lower()


def test_shape_exception_error() -> None:
    timeout_exc = httpx.ReadTimeout("Read timed out")
    msg = shape_exception_error(timeout_exc)
    assert "timed out" in msg.lower()
    assert "traceback" not in msg.lower()

    conn_exc = httpx.ConnectError("Failed to connect")
    msg_conn = shape_exception_error(conn_exc)
    assert "failed to establish connection" in msg_conn.lower()

    http_exc = httpx.HTTPError("Protocol error")
    msg_http = shape_exception_error(http_exc)
    assert "network or protocol error" in msg_http.lower()

    gen_exc = RuntimeError("Unexpected boom")
    msg_gen = shape_exception_error(gen_exc)
    assert "unexpected execution error" in msg_gen.lower()
