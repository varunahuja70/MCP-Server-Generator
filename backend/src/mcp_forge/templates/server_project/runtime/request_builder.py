"""Runtime HTTP request assembly: path interpolation, query formatting, headers, and bodies."""

import urllib.parse
from typing import Any


def build_request(
    base_url: str,
    path_template: str,
    arguments: dict[str, Any],
    param_locations: dict[str, str],
    is_flattened_body: bool = False,
    content_type: str = "application/json",
) -> tuple[str, dict[str, Any], dict[str, str], Any, Any]:
    """Assemble final URL, query params, headers, json_body, and form_body for an HTTP request.

    Returns:
        (final_url, query_params, headers, json_payload, form_payload)
    """
    headers: dict[str, str] = {}
    query_params: dict[str, Any] = {}
    path_params: dict[str, str] = {}
    body_fields: dict[str, Any] = {}

    for arg_name, arg_val in arguments.items():
        if arg_val is None:
            continue

        loc = param_locations.get(arg_name, "query")
        if loc == "path":
            path_params[arg_name] = urllib.parse.quote(str(arg_val), safe="")
        elif loc == "query":
            if isinstance(arg_val, list):
                # Standard explode=true array style
                query_params[arg_name] = [str(x) for x in arg_val]
            elif isinstance(arg_val, bool):
                query_params[arg_name] = "true" if arg_val else "false"
            else:
                query_params[arg_name] = str(arg_val)
        elif loc == "header":
            headers[arg_name] = str(arg_val)
        elif loc == "body":
            if is_flattened_body:
                body_fields[arg_name] = arg_val
            else:
                body_fields = arg_val if isinstance(arg_val, dict) else {"body": arg_val}

    # Interpolate path
    resolved_path = path_template
    for p_name, p_val in path_params.items():
        resolved_path = resolved_path.replace(f"{{{p_name}}}", p_val)

    # Disambiguate if parameter had location prefix (e.g. path_id -> id)
    if "{" in resolved_path:
        for p_name, p_val in path_params.items():
            bare_name = p_name.split("_", 1)[-1]
            resolved_path = resolved_path.replace(f"{{{bare_name}}}", p_val)

    clean_base = base_url.rstrip("/") if base_url else ""
    final_url = f"{clean_base}/{resolved_path.lstrip('/')}"

    json_payload = None
    form_payload = None

    if body_fields:
        if "form-urlencoded" in content_type.lower():
            form_payload = body_fields
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            json_payload = body_fields
            headers["Content-Type"] = "application/json"

    return final_url, query_params, headers, json_payload, form_payload
