"""Internal Representation (IR) data models for MCP Forge."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IRServer(BaseModel):
    """An API target server."""

    model_config = ConfigDict(extra="ignore")

    url: str
    description: str | None = None


class IRSecurityScheme(BaseModel):
    """Normalized security scheme definition."""

    model_config = ConfigDict(extra="ignore")

    name: str
    type: Literal["apiKey", "http", "oauth2", "openIdConnect", "mutualTLS", "other"]
    scheme: str | None = None
    in_loc: Literal["header", "query", "cookie"] | None = None
    param_name: str | None = None
    description: str | None = None
    bearer_format: str | None = None
    flows: dict[str, Any] | None = None


class IRParameter(BaseModel):
    """A parameter for an operation (path, query, header, or cookie)."""

    model_config = ConfigDict(extra="ignore")

    name: str
    in_loc: Literal["path", "query", "header", "cookie"]
    required: bool = False
    description: str | None = None
    schema_dict: dict[str, Any] = Field(default_factory=dict)
    deprecated: bool = False


class IRRequestBody(BaseModel):
    """A request payload definition."""

    model_config = ConfigDict(extra="ignore")

    required: bool = False
    content_type: str = "application/json"
    schema_dict: dict[str, Any] = Field(default_factory=dict)
    description: str | None = None


class IRResponse(BaseModel):
    """A response specification for a specific HTTP status code."""

    model_config = ConfigDict(extra="ignore")

    status_code: str
    description: str = ""
    content_type: str | None = None
    schema_dict: dict[str, Any] | None = None


class IROperation(BaseModel):
    """A normalized API operation."""

    model_config = ConfigDict(extra="ignore")

    operation_key: str
    method: str
    path: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    deprecated: bool = False
    parameters: list[IRParameter] = Field(default_factory=list)
    request_body: IRRequestBody | None = None
    responses: dict[str, IRResponse] = Field(default_factory=dict)
    security: list[dict[str, list[str]]] = Field(default_factory=list)
    unsupported_reason: str | None = None


class IRApi(BaseModel):
    """Normalized top-level API document."""

    model_config = ConfigDict(extra="ignore")

    title: str
    version: str
    description: str | None = None
    servers: list[IRServer] = Field(default_factory=list)
    security_schemes: dict[str, IRSecurityScheme] = Field(default_factory=dict)
    operations: list[IROperation] = Field(default_factory=list)


def make_operation_key(
    method: str,
    path: str,
    operation_id: str | None = None,
    existing_keys: set[str] | None = None,
) -> str:
    """Generate a stable, unique key for an operation.

    Prefers operation_id if clean and not already used; otherwise falls back to 'METHOD path'.
    """
    clean_method = method.upper().strip()
    clean_path = path.strip()
    key: str

    if operation_id and operation_id.strip():
        candidate = operation_id.strip()
        if existing_keys is None or candidate not in existing_keys:
            return candidate

    key = f"{clean_method} {clean_path}"
    if existing_keys is not None and key in existing_keys:
        suffix = 2
        while f"{key} ({suffix})" in existing_keys:
            suffix += 1
        key = f"{key} ({suffix})"

    return key
