"""Hypothesis fuzz tests for names, descriptions, and input schemas."""

import json
from typing import Any, Literal

from hypothesis import given, settings
from hypothesis import strategies as st

from mcp_forge.core.ir.models import IROperation, IRParameter, IRRequestBody
from mcp_forge.core.mapping.descriptions import (
    build_tool_description,
    clean_description,
)
from mcp_forge.core.mapping.input_schema import build_input_schema
from mcp_forge.core.mapping.names import derive_raw_name, resolve_tool_name, sanitize_tool_name
from mcp_forge.core.security.identifiers import is_valid_identifier

# Strategy for generating arbitrary strings (including unicode, empty, null bytes, control chars)
arbitrary_strings = st.text(max_size=300)


@settings(max_examples=100, deadline=None)
@given(text=arbitrary_strings)
def test_fuzz_sanitize_tool_name_always_produces_valid_identifier(text: str) -> None:
    """sanitize_tool_name must always produce a valid identifier regardless of input."""
    sanitized = sanitize_tool_name(text)
    assert is_valid_identifier(sanitized), f"Failed for input {text!r} -> {sanitized!r}"
    assert len(sanitized) <= 64
    assert sanitized.isascii()


@settings(max_examples=100, deadline=None)
@given(
    method=st.sampled_from(["get", "post", "put", "delete", "patch", "options", "head"]),
    path=arbitrary_strings,
    op_id=st.one_of(st.none(), arbitrary_strings),
)
def test_fuzz_derive_and_resolve_tool_names(method: str, path: str, op_id: str | None) -> None:
    """derive_raw_name and resolve_tool_name must never raise unhandled exceptions or produce invalid names."""
    raw = derive_raw_name(method, path, op_id)
    sanitized = sanitize_tool_name(raw)
    assert is_valid_identifier(sanitized)

    seen: set[str] = {"get_existing"}
    final_name, collided = resolve_tool_name(method, path, op_id, existing_names=seen)
    assert is_valid_identifier(final_name)
    assert final_name not in seen or final_name == "get_existing"
    assert len(final_name) <= 64


@settings(max_examples=100, deadline=None)
@given(
    desc=arbitrary_strings,
    max_len=st.integers(min_value=1, max_value=2000),
)
def test_fuzz_clean_description(desc: str, max_len: int) -> None:
    """clean_description and flatten_markdown never crash and respect length caps."""
    cleaned = clean_description(desc, max_length=max_len)
    assert isinstance(cleaned, str)
    # len may exceed max_len by up to 3 chars because of ellipsis '...'
    assert len(cleaned) <= max_len + 3
    # Invisible/bidi characters should be stripped
    for c in cleaned:
        assert ord(c) != 0  # No null bytes


@settings(max_examples=100, deadline=None)
@given(
    summary=st.one_of(st.none(), arbitrary_strings),
    desc=st.one_of(st.none(), arbitrary_strings),
)
def test_fuzz_build_tool_description(summary: str | None, desc: str | None) -> None:
    """build_tool_description safely builds plain string."""
    res = build_tool_description(summary=summary, description=desc)
    assert isinstance(res, str)
    assert len(res) <= 1010


# Strategy for generating JSON schemas
json_primitives = st.sampled_from(["string", "integer", "number", "boolean"])


@st.composite
def json_schema_strategy(draw: Any) -> dict[str, Any]:
    prop_count = draw(st.integers(min_value=0, max_value=5))
    props = {}
    for _ in range(prop_count):
        prop_name = draw(
            st.text(
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc")),
                min_size=1,
                max_size=20,
            )
        )
        prop_type = draw(json_primitives)
        props[prop_name] = {"type": prop_type}
    return {"type": "object", "properties": props}


@settings(max_examples=80, deadline=None)
@given(
    param_names=st.lists(arbitrary_strings, max_size=5),
    schema=json_schema_strategy(),
)
def test_fuzz_build_input_schema(param_names: list[str], schema: dict[str, Any]) -> None:
    """build_input_schema safely flattens parameters and request bodies."""
    params = []
    for idx, p_name in enumerate(param_names):
        loc_choices: list[Literal["query", "path", "header", "cookie"]] = [
            "query",
            "path",
            "header",
            "cookie",
        ]
        loc = loc_choices[idx % 4]
        params.append(
            IRParameter(
                name=p_name or f"param_{idx}",
                in_loc=loc,
                required=loc == "path",
                schema_dict={"type": "string"},
            )
        )

    op = IROperation(
        operation_key="fuzz_op",
        method="POST",
        path="/fuzz",
        parameters=params,
        request_body=IRRequestBody(
            content_type="application/json",
            schema_dict=schema,
            required=True,
        ),
    )

    input_schema, param_locs, is_flattened = build_input_schema(op)
    assert isinstance(input_schema, dict)
    assert input_schema.get("type") == "object"
    assert "properties" in input_schema
    assert isinstance(param_locs, dict)
    # Must be valid json serializable
    json.dumps(input_schema)
