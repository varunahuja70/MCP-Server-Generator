"""Build flat input schema for MCP tools combining parameters and request bodies."""

from typing import Any

from mcp_forge.core.ir.models import IROperation
from mcp_forge.core.mapping.descriptions import clean_description


def build_input_schema(
    operation: IROperation,
    max_flatten_body_props: int = 8,
) -> tuple[dict[str, Any], dict[str, str], bool]:
    """Construct a flat JSON Schema object for tool arguments.

    Returns:
        (input_schema, param_locations, is_flattened_body)
        where param_locations maps argument name -> 'path' | 'query' | 'header' | 'cookie' | 'body'
    """
    properties: dict[str, Any] = {}
    required_set: set[str] = set()
    param_locations: dict[str, str] = {}
    seen_param_names: set[str] = set()

    # 1. Process parameters
    for p in operation.parameters:
        p_name = p.name
        # Disambiguate if parameter name clashes across locations
        if p_name in seen_param_names:
            prop_name = f"{p.in_loc}_{p_name}"
        else:
            prop_name = p_name
        seen_param_names.add(p_name)

        p_schema = dict(p.schema_dict) if p.schema_dict else {"type": "string"}
        if p.description:
            p_schema["description"] = clean_description(p.description, max_length=300)

        properties[prop_name] = p_schema
        param_locations[prop_name] = p.in_loc

        if p.required or p.in_loc == "path":
            required_set.add(prop_name)

    # 2. Process request body
    is_flattened_body = False
    if operation.request_body:
        body_schema = operation.request_body.schema_dict
        body_props = body_schema.get("properties") if isinstance(body_schema, dict) else None

        can_flatten = (
            isinstance(body_props, dict)
            and len(body_props) <= max_flatten_body_props
            and not any(k in properties for k in body_props)
        )

        if can_flatten and isinstance(body_props, dict):
            is_flattened_body = True
            body_required = set(body_schema.get("required", []))
            for b_name, b_val in body_props.items():
                b_schema = dict(b_val) if isinstance(b_val, dict) else {"type": "string"}
                properties[b_name] = b_schema
                param_locations[b_name] = "body"
                if b_name in body_required:
                    required_set.add(b_name)
        else:
            is_flattened_body = False
            b_schema = dict(body_schema) if body_schema else {"type": "object"}
            if operation.request_body.description:
                b_schema["description"] = clean_description(
                    operation.request_body.description, max_length=300
                )
            properties["body"] = b_schema
            param_locations["body"] = "body"
            if operation.request_body.required:
                required_set.add("body")

    schema_dict: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required_set:
        schema_dict["required"] = sorted(required_set)

    return schema_dict, param_locations, is_flattened_body
