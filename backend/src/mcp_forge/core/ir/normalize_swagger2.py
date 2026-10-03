"""Normalize Swagger 2.0 specification into MCP Forge Internal Representation (IR)."""

from typing import Any

from mcp_forge.core.ir.models import (
    IRApi,
    IROperation,
    IRParameter,
    IRRequestBody,
    IRResponse,
    IRSecurityScheme,
    IRServer,
    make_operation_key,
)
from mcp_forge.core.ir.schema_tools import to_json_schema

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}


def _build_parameter_schema(param: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    """Extract and build JSON Schema for a Swagger 2 parameter."""
    if "schema" in param and isinstance(param["schema"], dict):
        return to_json_schema(param["schema"], root=root)

    schema: dict[str, Any] = {}
    for key in (
        "type",
        "format",
        "items",
        "enum",
        "default",
        "maximum",
        "minimum",
        "maxLength",
        "minLength",
        "pattern",
        "multipleOf",
    ):
        if key in param:
            schema[key] = param[key]

    if not schema:
        schema["type"] = "string"

    return to_json_schema(schema, root=root)


def normalize_swagger2(doc: dict[str, Any]) -> IRApi:
    """Transform a Swagger 2.0 dictionary into an IRApi instance."""
    info = doc.get("info", {})
    title = str(info.get("title", "API"))
    version = str(info.get("version", "1.0.0"))
    description = info.get("description")

    # Servers
    servers: list[IRServer] = []
    host = doc.get("host")
    base_path = doc.get("basePath", "")
    schemes = doc.get("schemes", ["https"])
    if host:
        for scheme in schemes:
            servers.append(IRServer(url=f"{scheme}://{host}{base_path}".rstrip("/")))
    elif base_path:
        servers.append(IRServer(url=base_path))

    # Security schemes (securityDefinitions)
    sec_schemes: dict[str, IRSecurityScheme] = {}
    for name, sec_def in doc.get("securityDefinitions", {}).items():
        if not isinstance(sec_def, dict):
            continue
        stype = sec_def.get("type", "other")
        if stype == "basic":
            sec_schemes[name] = IRSecurityScheme(
                name=name,
                type="http",
                scheme="basic",
                description=sec_def.get("description"),
            )
        elif stype == "apiKey":
            sec_schemes[name] = IRSecurityScheme(
                name=name,
                type="apiKey",
                in_loc=sec_def.get("in"),
                param_name=sec_def.get("name"),
                description=sec_def.get("description"),
            )
        elif stype == "oauth2":
            sec_schemes[name] = IRSecurityScheme(
                name=name,
                type="oauth2",
                description=sec_def.get("description"),
                flows={"flow": sec_def.get("flow"), "scopes": sec_def.get("scopes")},
            )
        else:
            sec_schemes[name] = IRSecurityScheme(
                name=name,
                type="other",
                description=sec_def.get("description"),
            )

    # Operations
    operations: list[IROperation] = []
    seen_keys: set[str] = set()

    paths = doc.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_params: list[dict[str, Any]] = path_item.get("parameters", [])

        for method_name, op_item in path_item.items():
            if method_name.lower() not in HTTP_METHODS or not isinstance(op_item, dict):
                continue

            method = method_name.lower()
            op_id = op_item.get("operationId")
            op_key = make_operation_key(method, path, op_id, seen_keys)
            seen_keys.add(op_key)

            # Combine path-level and operation-level parameters
            raw_params = list(path_params) + list(op_item.get("parameters", []))
            params: list[IRParameter] = []
            request_body: IRRequestBody | None = None
            form_properties: dict[str, Any] = {}
            form_required: list[str] = []
            has_file_upload = False

            for p in raw_params:
                if not isinstance(p, dict):
                    continue
                in_loc = p.get("in")
                p_name = p.get("name", "")

                if in_loc == "body":
                    body_schema = _build_parameter_schema(p, root=doc)
                    request_body = IRRequestBody(
                        required=bool(p.get("required", False)),
                        content_type="application/json",
                        schema_dict=body_schema,
                        description=p.get("description"),
                    )
                elif in_loc == "formData":
                    if p.get("type") == "file":
                        has_file_upload = True
                    p_schema = _build_parameter_schema(p, root=doc)
                    form_properties[p_name] = p_schema
                    if p.get("required"):
                        form_required.append(p_name)
                elif in_loc in ("path", "query", "header", "cookie"):
                    params.append(
                        IRParameter(
                            name=p_name,
                            in_loc=in_loc,
                            required=bool(p.get("required", in_loc == "path")),
                            description=p.get("description"),
                            schema_dict=_build_parameter_schema(p, root=doc),
                            deprecated=bool(p.get("deprecated", False)),
                        )
                    )

            if form_properties and not request_body:
                form_schema: dict[str, Any] = {
                    "type": "object",
                    "properties": form_properties,
                }
                if form_required:
                    form_schema["required"] = form_required
                content_type = (
                    "multipart/form-data"
                    if has_file_upload
                    else "application/x-www-form-urlencoded"
                )
                request_body = IRRequestBody(
                    required=bool(form_required),
                    content_type=content_type,
                    schema_dict=form_schema,
                )

            # Responses
            responses: dict[str, IRResponse] = {}
            for code_str, resp_item in op_item.get("responses", {}).items():
                if not isinstance(resp_item, dict):
                    continue
                resp_schema = None
                if "schema" in resp_item and isinstance(resp_item["schema"], dict):
                    resp_schema = to_json_schema(resp_item["schema"], root=doc)

                responses[str(code_str)] = IRResponse(
                    status_code=str(code_str),
                    description=str(resp_item.get("description", "")),
                    content_type="application/json" if resp_schema else None,
                    schema_dict=resp_schema,
                )

            unsupported_reason = None
            if has_file_upload:
                unsupported_reason = "Multipart file uploads are not supported in V1"

            operations.append(
                IROperation(
                    operation_key=op_key,
                    method=method,
                    path=path,
                    operation_id=op_id,
                    summary=op_item.get("summary"),
                    description=op_item.get("description"),
                    tags=list(op_item.get("tags", [])),
                    deprecated=bool(op_item.get("deprecated", False)),
                    parameters=params,
                    request_body=request_body,
                    responses=responses,
                    security=list(op_item.get("security", doc.get("security", []))),
                    unsupported_reason=unsupported_reason,
                )
            )

    return IRApi(
        title=title,
        version=version,
        description=description,
        servers=servers,
        security_schemes=sec_schemes,
        operations=operations,
    )
