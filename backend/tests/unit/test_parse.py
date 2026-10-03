"""Unit tests for specification parsing, version detection, ref resolution, and validation."""

from pathlib import Path
from typing import Any

import pytest

from mcp_forge.core.parse import (
    count_operations,
    detect_spec_kind,
    load_spec_dict,
    lookup_local_ref,
    parse_and_validate,
    resolve_refs,
    validate_spec,
)
from mcp_forge.errors import InvalidSpecError

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "samples"


def test_detect_spec_kind_swagger2() -> None:
    data = {"swagger": "2.0", "info": {"title": "Test", "version": "1.0"}}
    assert detect_spec_kind(data) == "swagger2"


def test_detect_spec_kind_oas30() -> None:
    data = {"openapi": "3.0.1", "info": {"title": "Test", "version": "1.0"}}
    assert detect_spec_kind(data) == "oas30"


def test_detect_spec_kind_oas31() -> None:
    data = {"openapi": "3.1.0", "info": {"title": "Test", "version": "1.0"}}
    assert detect_spec_kind(data) == "oas31"


def test_detect_spec_kind_oas32() -> None:
    data = {"openapi": "3.2.0-draft", "info": {"title": "Test", "version": "1.0"}}
    assert detect_spec_kind(data) == "oas32"


def test_detect_spec_kind_invalid() -> None:
    with pytest.raises(InvalidSpecError, match="Unrecognized specification standard"):
        detect_spec_kind({"info": {"title": "Test"}})


def test_load_spec_dict_empty() -> None:
    with pytest.raises(InvalidSpecError, match="Specification text is empty"):
        load_spec_dict("   \n  ")


def test_load_spec_dict_not_a_mapping() -> None:
    with pytest.raises(InvalidSpecError, match="must be a JSON/YAML mapping"):
        load_spec_dict("- item1\n- item2")


def test_lookup_local_ref() -> None:
    root = {
        "components": {
            "schemas": {
                "User": {"type": "object", "properties": {"name": {"type": "string"}}},
                "Path/With~Slash": {"type": "integer"},
            }
        },
        "items": ["first", "second"],
    }

    user = lookup_local_ref(root, "#/components/schemas/User")
    assert user["type"] == "object"

    escaped = lookup_local_ref(root, "#/components/schemas/Path~1With~0Slash")
    assert escaped["type"] == "integer"

    second = lookup_local_ref(root, "#/items/1")
    assert second == "second"


def test_lookup_local_ref_not_found() -> None:
    root: dict[str, Any] = {"components": {"schemas": {}}}
    with pytest.raises(InvalidSpecError, match="key 'Missing' not found"):
        lookup_local_ref(root, "#/components/schemas/Missing")


def test_remote_ref_blocked() -> None:
    root = {"$ref": "https://example.com/schemas/user.json"}
    with pytest.raises(InvalidSpecError, match="Remote \\$ref resolution is disabled"):
        resolve_refs(root, root=root, allow_remote=False)


def test_validation_error_with_json_pointer() -> None:
    bad_spec = {
        "openapi": "3.1.0",
        "info": {"title": "Missing version"},
        # paths is missing
    }
    with pytest.raises(InvalidSpecError) as exc_info:
        validate_spec(bad_spec, "oas31")

    assert "Validation failed at" in exc_info.value.message
    details = exc_info.value.details or {}
    assert "errors" in details
    assert len(details["errors"]) > 0
    assert any("/paths" in err["path"] or "/info" in err["path"] for err in details["errors"])


def test_golden_sample_bookshop() -> None:
    bookshop_path = SAMPLES_DIR / "bookshop.openapi.yaml"
    text = bookshop_path.read_text(encoding="utf-8")
    parsed = parse_and_validate(text)

    assert parsed.kind == "oas31"
    assert parsed.title == "Bookshop API"
    assert (
        parsed.operation_count == 7
    )  # GET/POST /books, GET/PUT/DELETE /books/{book_id}, GET/POST /orders
    assert count_operations(parsed.raw_dict) == 7


def test_golden_sample_tasks() -> None:
    tasks_path = SAMPLES_DIR / "tasks.openapi.json"
    text = tasks_path.read_text(encoding="utf-8")
    parsed = parse_and_validate(text)

    assert parsed.kind == "oas30"
    assert parsed.title == "Tasks API"
    assert parsed.operation_count == 5  # GET/POST /tasks, GET/PATCH/DELETE /tasks/{task_id}


def test_golden_sample_legacy_swagger() -> None:
    swagger_path = SAMPLES_DIR / "legacy-swagger2.json"
    text = swagger_path.read_text(encoding="utf-8")
    parsed = parse_and_validate(text)

    assert parsed.kind == "swagger2"
    assert parsed.title == "Legacy Pet Inventory"
    assert parsed.operation_count == 4  # GET/POST /pets, GET/DELETE /pets/{id}
