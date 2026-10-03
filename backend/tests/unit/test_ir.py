"""Unit tests for Internal Representation (IR) normalization and schema tools."""

from typing import Any

from mcp_forge.core.ir import (
    cap_schema_size,
    merge_all_of,
    normalize_nullable,
    normalize_spec,
    to_json_schema,
)
from mcp_forge.core.ir.models import make_operation_key


def test_merge_all_of() -> None:
    schema = {
        "allOf": [
            {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
            {"properties": {"age": {"type": "integer"}}, "required": ["age"]},
        ],
        "description": "Person object",
    }
    merged = merge_all_of(schema)
    assert merged["type"] == "object"
    assert "name" in merged["properties"]
    assert "age" in merged["properties"]
    assert sorted(merged["required"]) == ["age", "name"]
    assert merged["description"] == "Person object"
    assert "allOf" not in merged


def test_normalize_nullable() -> None:
    schema_oas30 = {"type": "string", "nullable": True}
    normalized = normalize_nullable(schema_oas30)
    assert normalized["type"] == ["string", "null"]
    assert "nullable" not in normalized

    schema_already_null = {"type": ["string", "null"], "nullable": True}
    norm_already = normalize_nullable(schema_already_null)
    assert norm_already["type"] == ["string", "null"]


def test_cap_schema_size() -> None:
    # Build a deep schema with many properties
    props: dict[str, Any] = {f"field_{i}": {"type": "string"} for i in range(200)}
    schema = {"type": "object", "properties": props}

    capped = cap_schema_size(schema, max_nodes=50)
    assert capped.get("x-truncated") is True
    assert len(capped["properties"]) <= 10


def test_to_json_schema_depth_and_cycle() -> None:
    root: dict[str, Any] = {
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "val": {"type": "string"},
                        "next": {"$ref": "#/components/schemas/Node"},
                    },
                }
            }
        }
    }

    res = to_json_schema(root["components"]["schemas"]["Node"], root=root, max_depth=4)
    assert res["type"] == "object"
    assert "val" in res["properties"]
    # The self-referencing next should either be cut or marked circular
    next_node = res["properties"]["next"]
    assert "val" in next_node["properties"]
    assert "x-circular-ref" in next_node["properties"]["next"]


def test_operation_key_stability() -> None:
    seen: set[str] = set()
    key1 = make_operation_key("get", "/books", "listBooks", seen)
    seen.add(key1)
    key2 = make_operation_key("get", "/books", "listBooks", seen)
    assert key1 == "listBooks"
    assert key2 == "GET /books"  # Disambiguated duplicate

    # Stability across repeated calls
    assert make_operation_key("post", "/books") == "POST /books"
    assert make_operation_key("post", "/books") == "POST /books"


def test_swagger2_oas30_oas31_oas32_equivalent_normalization() -> None:
    """The same logical API expressed across Swagger 2.0, 3.0, 3.1 and 3.2 normalizes to equivalent IR."""
    swagger2_doc = {
        "swagger": "2.0",
        "info": {"title": "Pet API", "version": "1.0.0", "description": "Test pet store"},
        "host": "api.example.com",
        "basePath": "/v1",
        "schemes": ["https"],
        "securityDefinitions": {
            "ApiKeyAuth": {"type": "apiKey", "name": "X-API-KEY", "in": "header"}
        },
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "findPets",
                    "summary": "Find all pets",
                    "parameters": [
                        {"name": "tag", "in": "query", "type": "string", "required": False}
                    ],
                    "responses": {
                        "200": {
                            "description": "Pet list",
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/definitions/Pet"},
                            },
                        }
                    },
                },
                "post": {
                    "operationId": "addPet",
                    "summary": "Add new pet",
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {"$ref": "#/definitions/Pet"},
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "Pet created",
                            "schema": {"$ref": "#/definitions/Pet"},
                        }
                    },
                },
            },
            "/pets/{id}": {
                "get": {
                    "operationId": "getPetById",
                    "parameters": [
                        {"name": "id", "in": "path", "type": "string", "required": True}
                    ],
                    "responses": {
                        "200": {
                            "description": "Pet details",
                            "schema": {"$ref": "#/definitions/Pet"},
                        }
                    },
                }
            },
        },
        "definitions": {
            "Pet": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                },
            }
        },
    }

    oas30_doc = {
        "openapi": "3.0.3",
        "info": {"title": "Pet API", "version": "1.0.0", "description": "Test pet store"},
        "servers": [{"url": "https://api.example.com/v1"}],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {"type": "apiKey", "name": "X-API-KEY", "in": "header"}
            },
            "schemas": {
                "Pet": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                }
            },
        },
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "findPets",
                    "summary": "Find all pets",
                    "parameters": [
                        {
                            "name": "tag",
                            "in": "query",
                            "schema": {"type": "string"},
                            "required": False,
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Pet list",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Pet"},
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "operationId": "addPet",
                    "summary": "Add new pet",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Pet created",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}
                            },
                        }
                    },
                },
            },
            "/pets/{id}": {
                "get": {
                    "operationId": "getPetById",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Pet details",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}
                            },
                        }
                    },
                }
            },
        },
    }

    oas31_doc = dict(oas30_doc)
    oas31_doc["openapi"] = "3.1.0"

    oas32_doc = dict(oas30_doc)
    oas32_doc["openapi"] = "3.2.0-draft"

    # Normalize all 4 versions
    ir_sw2 = normalize_spec(swagger2_doc)
    ir_30 = normalize_spec(oas30_doc)
    ir_31 = normalize_spec(oas31_doc)
    ir_32 = normalize_spec(oas32_doc)

    irs = [ir_sw2, ir_30, ir_31, ir_32]

    # Verify identical core API info
    for ir in irs:
        assert ir.title == "Pet API"
        assert ir.version == "1.0.0"
        assert len(ir.operations) == 3

    # Check operation keys across all 4 versions
    for ir in irs:
        keys = [op.operation_key for op in ir.operations]
        assert "findPets" in keys
        assert "addPet" in keys
        assert "getPetById" in keys

    # Check security scheme mapping
    for ir in irs:
        assert "ApiKeyAuth" in ir.security_schemes
        sec = ir.security_schemes["ApiKeyAuth"]
        assert sec.type == "apiKey"
        assert sec.in_loc == "header"
        assert sec.param_name == "X-API-KEY"

    # Check parameters and body on findPets and addPet
    for ir in irs:
        find_op = next(op for op in ir.operations if op.operation_key == "findPets")
        assert len(find_op.parameters) == 1
        assert find_op.parameters[0].name == "tag"
        assert find_op.parameters[0].in_loc == "query"

        add_op = next(op for op in ir.operations if op.operation_key == "addPet")
        assert add_op.request_body is not None
        assert add_op.request_body.required is True
        assert add_op.request_body.schema_dict.get("type") == "object"
        assert "name" in add_op.request_body.schema_dict.get("properties", {})
