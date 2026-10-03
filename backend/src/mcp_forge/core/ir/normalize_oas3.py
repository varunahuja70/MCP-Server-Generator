"""Normalize OpenAPI 3.0 / 3.1 / 3.2 specification into MCP Forge Internal Representation (IR)."""

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


def normalize_oas3(doc: dict[str, Any]) -> IRApi:
    """Transform an OpenAPI 3.x dictionary into an IRApi instance."""
    info = doc.get("info", {})
    title = str(info.get("title", "API"))
    version = str(info.get("version", "1.0.0"))
    description = info.get("description")

    # Servers
    servers: list[IRServer] = []
    for s in doc.get("servers", []):
        if isinstance(s, dict) and "url" in s:
            servers.append(IRServer(url=str(s["url"]), description=s.get("description")))

    # Security schemes (components.securitySchemes)
    sec_schemes: dict[str, IRSecurityScheme] = {}
    components = doc.get("components", {})
    for name, sec_def in components.get("securitySchemes", {}).items():
        if not isinstance(sec_def, dict):
            continue
        raw_type = sec_def.get("type", "other")
        stype = (
            raw_type
            if raw_type in ("apiKey", "http", "oauth2", "openIdConnect", "mutualTLS")
            else "other"
        )

        sec_schemes[name] = IRSecurityScheme(
            name=name,
            type=stype,  # type: ignore[arg-type]
            scheme=sec_def.get("scheme"),
            in_loc=sec_def.get("in"),
            param_name=sec_def.get("name"),
            description=sec_def.get("description"),
            bearer_format=sec_def.get("bearerFormat"),
            flows=sec_def.get("flows"),
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

            # Parameters
            raw_params = list(path_params) + list(op_item.get("parameters", []))
            params: list[IRParameter] = []
            for p in raw_params:
                if not isinstance(p, dict):
                    continue
                in_loc = p.get("in")
                if in_loc not in ("path", "query", "header", "cookie"):
                    continue

                schema_obj = p.get("schema", {})
                params.append(
                    IRParameter(
                        name=p.get("name", ""),
                        in_loc=in_loc,
                        required=bool(p.get("required", in_loc == "path")),
                        description=p.get("description"),
                        schema_dict=to_json_schema(schema_obj, root=doc),
                        deprecated=bool(p.get("deprecated", False)),
                    )
                )

            # Request Body
            request_body: IRRequestBody | None = None
            raw_body = op_item.get("requestBody")
            unsupported_reason: str | None = None

            if isinstance(raw_body, dict):
                content = raw_body.get("content", {})
                req_content_type = "application/json"
                target_content = None

                if "application/json" in content:
                    req_content_type = "application/json"
                    target_content = content["application/json"]
                elif "application/x-www-form-urlencoded" in content:
                    req_content_type = "application/x-www-form-urlencoded"
                    target_content = content["application/x-www-form-urlencoded"]
                elif "multipart/form-data" in content:
                    req_content_type = "multipart/form-data"
                    target_content = content["multipart/form-data"]
                    unsupported_reason = "Multipart and file uploads are not supported in V1"
                elif content:
                    req_content_type = next(iter(content.keys()))
                    target_content = content[req_content_type]

                if isinstance(target_content, dict):
                    body_schema = target_content.get("schema", {})
                    request_body = IRRequestBody(
                        required=bool(raw_body.get("required", False)),
                        content_type=req_content_type,
                        schema_dict=to_json_schema(body_schema, root=doc),
                        description=raw_body.get("description"),
                    )

            # Responses
            responses: dict[str, IRResponse] = {}
            for code_str, resp_item in op_item.get("responses", {}).items():
                if not isinstance(resp_item, dict):
                    continue

                content = resp_item.get("content", {})
                resp_content_type = None
                resp_schema = None

                if isinstance(content, dict) and content:
                    if "application/json" in content:
                        resp_content_type = "application/json"
                        resp_schema = to_json_schema(
                            content["application/json"].get("schema"), root=doc
                        )
                    else:
                        resp_content_type = next(iter(content.keys()))
                        first_content = content[resp_content_type]
                        if isinstance(first_content, dict):
                            resp_schema = to_json_schema(first_content.get("schema"), root=doc)

                responses[str(code_str)] = IRResponse(
                    status_code=str(code_str),
                    description=str(resp_item.get("description", "")),
                    content_type=resp_content_type,
                    schema_dict=resp_schema,
                )

            # Security
            op_security = op_item.get("security", doc.get("security", []))

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
                    security=list(op_security) if isinstance(op_security, list) else [],
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
