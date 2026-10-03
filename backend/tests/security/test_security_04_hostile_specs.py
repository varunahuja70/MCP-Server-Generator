"""Security Test 4: Hostile specifications (alias bomb, deep nesting, circular $ref).

Requirements from docs/03-security.md Section 11 Test 4:
"YAML alias bomb, deeply nested JSON/YAML, huge file, circular $ref, self-referencing allOf:
 all fail fast with clear errors under the time limit."
"""

import time
from pathlib import Path

import pytest

from mcp_forge.core.parse import load_spec_dict, parse_and_validate, resolve_refs
from mcp_forge.errors import InvalidSpecError

HOSTILE_DIR = Path(__file__).resolve().parent.parent.parent / "samples" / "hostile"


def test_yaml_alias_bomb_fails_fast() -> None:
    bomb_path = HOSTILE_DIR / "alias-bomb.yaml"
    text = bomb_path.read_text(encoding="utf-8")

    start = time.perf_counter()
    with pytest.raises(InvalidSpecError, match="alias count exceeded safety limit"):
        load_spec_dict(text)
    duration = time.perf_counter() - start

    assert duration < 1.0, f"Alias bomb check took {duration:.3f}s, expected < 1.0s"


def test_deep_nesting_fails_fast() -> None:
    nesting_path = HOSTILE_DIR / "deep-nesting.yaml"
    text = nesting_path.read_text(encoding="utf-8")

    start = time.perf_counter()
    with pytest.raises(InvalidSpecError, match="nesting depth exceeded safety limit"):
        load_spec_dict(text)
    duration = time.perf_counter() - start

    assert duration < 1.0, f"Deep nesting check took {duration:.3f}s, expected < 1.0s"


def test_circular_refs_terminate_safely() -> None:
    circular_path = HOSTILE_DIR / "circular-refs.yaml"
    text = circular_path.read_text(encoding="utf-8")

    start = time.perf_counter()
    parsed = parse_and_validate(text, validate=False)
    duration = time.perf_counter() - start

    assert duration < 1.0, f"Circular ref resolution took {duration:.3f}s, expected < 1.0s"
    schema = parsed.resolved_dict["paths"]["/loop"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    # The circular reference should be terminated
    node_b = schema["properties"]["next"]
    assert "x-circular-ref" in node_b["properties"]["next"]


def test_self_referencing_ref_terminates_safely() -> None:
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Self Ref", "version": "1.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Tree": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "self": {"$ref": "#/components/schemas/Tree"},
                    },
                }
            }
        },
    }

    start = time.perf_counter()
    resolved = resolve_refs(spec, root=spec)
    duration = time.perf_counter() - start

    assert duration < 1.0
    tree_schema = resolved["components"]["schemas"]["Tree"]
    assert "x-circular-ref" in tree_schema["properties"]["self"]["properties"]["self"]


def test_hostile_names_parse_without_code_execution() -> None:
    names_path = HOSTILE_DIR / "hostile-names.yaml"
    text = names_path.read_text(encoding="utf-8")

    # Should safely parse and validate as normal YAML/dict, without executing any payload
    parsed = parse_and_validate(text, validate=False)
    op = parsed.resolved_dict["paths"]["/malicious/{id}"]["get"]
    assert "import os" in op["operationId"]
