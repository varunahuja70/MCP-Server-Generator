"""Unit and integration tests for Mock API router, data generator, and in-process server."""

from pathlib import Path

import httpx
import jsonschema
import pytest

from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.mock_api.builder import MockApiBuilder
from mcp_forge.mock_api.data_gen import MockDataGenerator
from mcp_forge.mock_api.server import MockServer

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


def test_mock_data_generator_primitives() -> None:
    """MockDataGenerator produces data conforming to schema types and formats."""
    gen = MockDataGenerator(seed=123)

    assert isinstance(gen.generate({"type": "string"}), str)
    assert gen.generate({"type": "string", "format": "date"}) == "2026-01-15"
    assert gen.generate({"type": "string", "format": "email"}) == "user@example.com"
    assert isinstance(gen.generate({"type": "integer", "minimum": 10}), int)
    assert gen.generate({"type": "integer", "minimum": 10}) >= 10
    assert gen.generate({"type": "boolean"}) is True

    arr = gen.generate({"type": "array", "items": {"type": "string"}, "minItems": 2})
    assert isinstance(arr, list)
    assert len(arr) >= 2
    assert isinstance(arr[0], str)

    obj = gen.generate(
        {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"},
            },
            "required": ["id", "title"],
        }
    )
    assert isinstance(obj, dict)
    assert "id" in obj and isinstance(obj["id"], int)
    assert "title" in obj and isinstance(obj["title"], str)


@pytest.mark.parametrize(
    "sample_file",
    [
        "bookshop.openapi.yaml",
        "tasks.openapi.json",
        "legacy-swagger2.json",
    ],
)
def test_all_sample_operations_validate_against_response_schemas(sample_file: str) -> None:
    """For each sample, every operation returns a response validating against its documented schema."""
    raw_text = (SAMPLE_DIR / sample_file).read_text(encoding="utf-8")
    parsed = parse_and_validate(raw_text)
    ir = normalize_spec(parsed)

    builder = MockApiBuilder(ir)

    for op in ir.operations:
        # Replace path parameters with dummy values for request dispatch
        dispatch_path = op.path
        for p in op.parameters:
            if p.in_loc == "path":
                dispatch_path = dispatch_path.replace(f"{{{p.name}}}", "test1234")

        status, headers, resp_body = builder.handle_request(
            method=op.method,
            path=dispatch_path,
        )

        assert status in (200, 201, 202, 204), (
            f"Unexpected status {status} for {op.method} {op.path}"
        )

        # If 204 No Content, body must be None
        if status == 204:
            assert resp_body is None
            continue

        # Check response against documented schema
        resp_spec = op.responses.get(str(status))
        if resp_spec and resp_spec.schema_dict:
            jsonschema.validate(instance=resp_body, schema=resp_spec.schema_dict)


def test_mock_api_status_override() -> None:
    """X-Mock-Status header triggers simulated error responses."""
    raw_text = (SAMPLE_DIR / "tasks.openapi.json").read_text(encoding="utf-8")
    parsed = parse_and_validate(raw_text)
    ir = normalize_spec(parsed)
    builder = MockApiBuilder(ir)

    status, _, resp_body = builder.handle_request(
        method="GET",
        path="/tasks",
        headers={"X-Mock-Status": "500"},
    )
    assert status == 500
    assert "error" in resp_body or "status" in resp_body


@pytest.mark.asyncio
async def test_in_process_mock_server_lifecycle() -> None:
    """In-process mock server starts on loopback, responds to HTTP requests, and shuts down."""
    raw_text = (SAMPLE_DIR / "bookshop.openapi.yaml").read_text(encoding="utf-8")
    parsed = parse_and_validate(raw_text)
    ir = normalize_spec(parsed)

    server = MockServer(ir)
    base_url = await server.start()
    assert base_url.startswith("http://127.0.0.1:")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base_url}/books")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, (dict, list))
    finally:
        await server.stop()
