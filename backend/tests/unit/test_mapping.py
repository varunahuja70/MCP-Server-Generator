"""Unit tests for tool mapping: names, descriptions, input schemas, and manifest validation."""

from mcp_forge.core.ir.models import IROperation, IRParameter, IRRequestBody
from mcp_forge.core.mapping import (
    ManifestDoc,
    ManifestInfo,
    ManifestTool,
    build_input_schema,
    build_tool_description,
    clean_description,
    resolve_tool_name,
    sanitize_tool_name,
    validate_manifest,
)
from mcp_forge.core.security.identifiers import is_valid_identifier


def test_naming_edge_cases_unicode() -> None:
    # Unicode and special symbols
    name = sanitize_tool_name("get_üser_dätä!@#")
    assert is_valid_identifier(name)
    assert name.startswith("get_")


def test_naming_edge_cases_long() -> None:
    # Extremely long name > 64 chars
    very_long = "a" * 100
    name = sanitize_tool_name(very_long)
    assert is_valid_identifier(name)
    assert len(name) <= 64


def test_naming_edge_cases_reserved() -> None:
    # Python reserved keywords
    for kw in ("def", "class", "import", "return", "server", "tools"):
        name = sanitize_tool_name(kw)
        assert is_valid_identifier(name)
        assert name != kw
        assert name.endswith(("_op", "_tool"))


def test_naming_edge_cases_duplicates() -> None:
    seen: set[str] = set()
    name1, coll1 = resolve_tool_name("get", "/users", "getUsers", existing_names=seen)
    seen.add(name1)
    name2, coll2 = resolve_tool_name("get", "/users", "getUsers", existing_names=seen)
    seen.add(name2)
    name3, coll3 = resolve_tool_name("get", "/users", "getUsers", existing_names=seen)

    assert name1 == "get_users"
    assert coll1 is False
    assert name2 == "get_users_2"
    assert coll2 is True
    assert name3 == "get_users_3"
    assert coll3 is True


def test_naming_leading_digits_and_prefix() -> None:
    name = sanitize_tool_name("123_test_action", prefix="my_api")
    assert is_valid_identifier(name)
    assert name.startswith("my_api_")


def test_clean_description_markdown_and_invisible() -> None:
    raw = "# Header\nThis is **bold** text with [link](https://example.com) and invisible \u200b\u200bspaces."
    cleaned = clean_description(raw)
    assert "#" not in cleaned
    assert "**" not in cleaned
    assert "[link]" not in cleaned
    assert "\u200b" not in cleaned
    assert "This is bold text with link and invisible spaces." in cleaned


def test_build_tool_description() -> None:
    desc = build_tool_description(
        summary="Get book",
        description="Retrieve a single book by id.",
        parameter_notes=["id (path): Book ID"],
    )
    assert "Get book" in desc
    assert "Retrieve a single book by id." in desc
    assert "Parameters: id (path): Book ID" in desc


def test_build_input_schema_flatten_small_body() -> None:
    op = IROperation(
        operation_key="POST /books",
        method="post",
        path="/books",
        parameters=[
            IRParameter(
                name="store_id", in_loc="query", required=True, schema_dict={"type": "string"}
            )
        ],
        request_body=IRRequestBody(
            required=True,
            content_type="application/json",
            schema_dict={
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title": {"type": "string"},
                    "price": {"type": "number"},
                },
            },
        ),
    )

    schema, locs, is_flattened = build_input_schema(op, max_flatten_body_props=8)
    assert is_flattened is True
    assert "store_id" in schema["properties"]
    assert "title" in schema["properties"]
    assert "price" in schema["properties"]
    assert "body" not in schema["properties"]
    assert locs["store_id"] == "query"
    assert locs["title"] == "body"
    assert "title" in schema["required"]
    assert "store_id" in schema["required"]


def test_manifest_validation() -> None:
    tool = ManifestTool(
        name="list_books",
        operation_key="GET /books",
        method="GET",
        path="/books",
        description="List all books in store",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        annotations={"read_only_hint": True},
        security=[],
        param_locations={},
        is_flattened_body=False,
    )

    doc = ManifestDoc(
        schema_version="1.0",
        info=ManifestInfo(title="Test", version="1.0.0", base_url="https://api.example.com"),
        auth={},
        tools=[tool],
    )

    # Validate against schema
    validate_manifest(doc.model_dump())
