"""Schema transformation tools: ref resolution, allOf merging, nullable normalization, depth cutting, and size capping."""

from copy import deepcopy
from typing import Any

from mcp_forge.core.parse.refs import lookup_local_ref


def normalize_nullable(schema: dict[str, Any]) -> dict[str, Any]:
    """Convert OpenAPI 3.0 'nullable: true' into standard JSON Schema type array."""
    if not isinstance(schema, dict):
        return schema

    res = dict(schema)
    if res.pop("nullable", False) is True:
        curr_type = res.get("type")
        if isinstance(curr_type, str):
            if curr_type != "null":
                res["type"] = [curr_type, "null"]
        elif isinstance(curr_type, list):
            if "null" not in curr_type:
                res["type"] = [*curr_type, "null"]
        elif "anyOf" in res and isinstance(res["anyOf"], list):
            null_present = any(
                isinstance(x, dict) and x.get("type") == "null" for x in res["anyOf"]
            )
            if not null_present:
                res["anyOf"] = [*res["anyOf"], {"type": "null"}]
        elif "oneOf" in res and isinstance(res["oneOf"], list):
            null_present = any(
                isinstance(x, dict) and x.get("type") == "null" for x in res["oneOf"]
            )
            if not null_present:
                res["oneOf"] = [*res["oneOf"], {"type": "null"}]
        elif "type" not in res:
            res["type"] = ["string", "number", "integer", "boolean", "array", "object", "null"]

    return res


def merge_all_of(schema: dict[str, Any]) -> dict[str, Any]:
    """Merge an allOf array into a single unified JSON Schema dictionary."""
    if not isinstance(schema, dict):
        return schema

    all_of = schema.get("allOf")
    if not isinstance(all_of, list):
        return schema

    merged: dict[str, Any] = {k: v for k, v in schema.items() if k != "allOf"}
    properties: dict[str, Any] = dict(merged.get("properties", {}))
    required_set: set[str] = set(merged.get("required", []))

    for sub in all_of:
        if not isinstance(sub, dict):
            continue
        sub_merged = merge_all_of(sub)

        # Merge type
        if "type" in sub_merged and "type" not in merged:
            merged["type"] = sub_merged["type"]

        # Merge description
        if "description" in sub_merged and "description" not in merged:
            merged["description"] = sub_merged["description"]

        # Merge properties
        sub_props = sub_merged.get("properties")
        if isinstance(sub_props, dict):
            properties.update(sub_props)

        # Merge required
        sub_req = sub_merged.get("required")
        if isinstance(sub_req, list):
            required_set.update(str(r) for r in sub_req)

    if properties:
        merged["properties"] = properties
        if "type" not in merged:
            merged["type"] = "object"

    if required_set:
        merged["required"] = sorted(required_set)

    return merged


def count_schema_nodes(node: Any) -> int:
    """Count the total number of dictionary and list nodes in a schema."""
    if isinstance(node, dict):
        return 1 + sum(count_schema_nodes(v) for v in node.values())
    elif isinstance(node, list):
        return 1 + sum(count_schema_nodes(v) for v in node)
    return 1


def cap_schema_size(node: Any, max_nodes: int = 500) -> Any:
    """Enforce a size limit on the schema AST by truncating excess properties."""
    total = count_schema_nodes(node)
    if total <= max_nodes:
        return node

    if isinstance(node, dict):
        truncated = dict(node)
        if "properties" in truncated and isinstance(truncated["properties"], dict):
            props = dict(truncated["properties"])
            # Keep only the first few properties to stay under limit
            keys = list(props.keys())[:10]
            truncated["properties"] = {k: props[k] for k in keys}
            truncated["x-truncated"] = True
            truncated["description"] = (
                str(truncated.get("description", ""))
                + " [Truncated: schema exceeded maximum complexity]"
            ).strip()
            return truncated

    return {
        "type": "object",
        "description": "Schema truncated: exceeded maximum complexity limit.",
        "x-truncated": True,
    }


def to_json_schema(
    schema: dict[str, Any] | None,
    root: dict[str, Any] | None = None,
    seen_refs: set[str] | None = None,
    current_depth: int = 0,
    max_depth: int = 6,
) -> dict[str, Any]:
    """Convert an OpenAPI/Swagger schema into a clean, standalone JSON Schema."""
    if not schema or not isinstance(schema, dict):
        return {"type": "object"}

    visited = set(seen_refs or set())

    if current_depth > max_depth:
        return {
            "type": "object",
            "description": "Schema simplified: exceeded maximum resolution depth.",
            "x-cut-depth": True,
        }

    # Handle $ref
    if "$ref" in schema and isinstance(schema["$ref"], str):
        ref = schema["$ref"]
        if ref in visited:
            return {
                "type": "object",
                "description": f"Circular reference to {ref}.",
                "x-circular-ref": ref,
            }

        if root and ref.startswith("#"):
            try:
                target = lookup_local_ref(root, ref)
                visited.add(ref)
                resolved = to_json_schema(
                    target,
                    root=root,
                    seen_refs=visited,
                    current_depth=current_depth + 1,
                    max_depth=max_depth,
                )
                # Sibling overrides
                merged = dict(resolved)
                for k, v in schema.items():
                    if k != "$ref":
                        merged[k] = v
                return normalize_nullable(merge_all_of(merged))
            except Exception:
                # Fallback if unresolvable
                return {"type": "object", "x-unresolved-ref": ref}
        else:
            return {"type": "object", "x-unresolved-ref": ref}

    # Recursively transform properties and sub-schemas
    res: dict[str, Any] = {}
    for k, v in schema.items():
        if k in ("properties", "$defs", "definitions") and isinstance(v, dict):
            res[k] = {
                prop_name: to_json_schema(
                    prop_val,
                    root=root,
                    seen_refs=visited,
                    current_depth=current_depth + 1,
                    max_depth=max_depth,
                )
                for prop_name, prop_val in v.items()
            }
        elif k in ("items", "additionalProperties") and isinstance(v, dict):
            res[k] = to_json_schema(
                v,
                root=root,
                seen_refs=visited,
                current_depth=current_depth + 1,
                max_depth=max_depth,
            )
        elif k in ("oneOf", "anyOf", "allOf") and isinstance(v, list):
            res[k] = [
                to_json_schema(
                    item,
                    root=root,
                    seen_refs=visited,
                    current_depth=current_depth + 1,
                    max_depth=max_depth,
                )
                if isinstance(item, dict)
                else item
                for item in v
            ]
        else:
            res[k] = deepcopy(v)

    res = normalize_nullable(res)
    res = merge_all_of(res)
    res = cap_schema_size(res)
    return res
