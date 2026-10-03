"""Unit tests for safe YAML parser, alias bomb and recursion limits."""

import pytest

from mcp_forge.core.security.safe_yaml import safe_load_yaml
from mcp_forge.errors import InvalidSpecError


def test_safe_yaml_loads_valid_document() -> None:
    doc = """
    openapi: "3.0.0"
    info:
      title: "Sample API"
      version: "1.0.0"
    paths:
      /users:
        get:
          summary: "List users"
    """
    data = safe_load_yaml(doc)
    assert data["openapi"] == "3.0.0"
    assert data["info"]["title"] == "Sample API"
    assert "/users" in data["paths"]


def test_yaml_alias_bomb_rejected() -> None:
    # Billion Laughs YAML bomb pattern
    bomb = """
    a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]
    b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
    c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
    d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
    e: [*d,*d,*d,*d,*d,*d,*d,*d,*d]
    """
    with pytest.raises(InvalidSpecError, match="YAML alias count exceeded"):
        safe_load_yaml(bomb, max_aliases=20)


def test_yaml_nesting_depth_limit() -> None:
    # Deeply nested YAML structure
    deep_yaml = "a:\n" + "  " * 1 + "b:\n" + "  " * 2 + "c:\n" + "  " * 3 + "d: end"
    # Should fail when max_depth is 2
    with pytest.raises(InvalidSpecError, match="YAML nesting depth exceeded"):
        safe_load_yaml(deep_yaml, max_depth=2)
