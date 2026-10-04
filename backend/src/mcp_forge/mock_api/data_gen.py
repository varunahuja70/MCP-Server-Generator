"""Deterministic fake data generator based on OpenAPI / JSON Schemas."""

import random
from typing import Any

# Default deterministic seed for reproducible mock responses
DEFAULT_SEED = 42


class MockDataGenerator:
    """Generate realistic fake data matching JSON schemas deterministically."""

    def __init__(self, seed: int = DEFAULT_SEED) -> None:
        self.rng = random.Random(seed)  # noqa: S311 - Deterministic mock data generation, not security cryptography

    def generate(self, schema: dict[str, Any] | None, depth: int = 0) -> Any:
        """Recursively generate fake data for schema, handling primitives, arrays, and objects."""
        if schema is None or not isinstance(schema, dict):
            return {}

        # 1. Use explicit example or examples if provided
        if "example" in schema:
            return schema["example"]
        if "examples" in schema and isinstance(schema["examples"], list) and schema["examples"]:
            return schema["examples"][0]

        # 2. Check enum
        if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
            return schema["enum"][0]

        # 3. Check const / default
        if "const" in schema:
            return schema["const"]
        if "default" in schema:
            return schema["default"]

        # Prevent runaway recursion
        if depth > 5:
            return {}

        # 4. Handle oneOf / anyOf
        if "oneOf" in schema and isinstance(schema["oneOf"], list) and schema["oneOf"]:
            return self.generate(schema["oneOf"][0], depth=depth + 1)
        if "anyOf" in schema and isinstance(schema["anyOf"], list) and schema["anyOf"]:
            return self.generate(schema["anyOf"][0], depth=depth + 1)
        if "allOf" in schema and isinstance(schema["allOf"], list):
            merged: dict[str, Any] = {}
            for sub in schema["allOf"]:
                val = self.generate(sub, depth=depth + 1)
                if isinstance(val, dict):
                    merged.update(val)
            return merged

        # 5. Type-based generation
        schema_type = schema.get("type", "object")

        if schema_type == "string":
            fmt = schema.get("format", "")
            if fmt == "date":
                return "2026-01-15"
            elif fmt == "date-time":
                return "2026-01-15T10:30:00Z"
            elif fmt == "email":
                return "user@example.com"
            elif fmt == "uri" or fmt == "url":
                return "https://example.com/item"
            elif fmt == "uuid":
                return "01948572-8888-7abc-9def-0123456789ab"
            return "sample_string"

        elif schema_type == "integer":
            min_v = schema.get("minimum", 1)
            max_v = schema.get("maximum", 100)
            return min_v if min_v <= max_v else 1

        elif schema_type == "number":
            min_v = schema.get("minimum", 1.0)
            return float(min_v)

        elif schema_type == "boolean":
            return True

        elif schema_type == "array":
            items_schema = schema.get("items", {})
            min_items = schema.get("minItems", 1)
            count = max(1, min_items)
            return [self.generate(items_schema, depth=depth + 1) for _ in range(count)]

        elif schema_type == "object" or "properties" in schema:
            res: dict[str, Any] = {}
            props = schema.get("properties", {})
            for p_name, p_schema in props.items():
                res[p_name] = self.generate(p_schema, depth=depth + 1)
            return res

        return {}
