"""Pydantic v2 schemas for all MCP Forge REST API requests and responses."""

from typing import Any, Literal

from pydantic import BaseModel, Field

# --- Shared / Common Models ---


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


# --- Samples ---


class SampleSummary(BaseModel):
    id: str
    title: str
    description: str
    filename: str
    format: str
    operation_count: int


class ProjectFromSampleRequest(BaseModel):
    sample_id: str
    name: str | None = None
    slug: str | None = None


# --- Projects ---


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    slug: str | None = Field(default=None, max_length=64)


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    slug: str | None = Field(default=None, max_length=64)


class ProjectDeleteRequest(BaseModel):
    confirm_slug: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: str
    updated_at: str
    archived_at: str | None = None
    operation_count: int = 0
    latest_build_status: str | None = None
    spec_version_count: int = 0


# --- Specs ---


class SpecCreateRequest(BaseModel):
    source_type: Literal["upload", "paste", "link"] = "paste"
    content: str | None = None  # text content when paste or upload
    url: str | None = None  # link url
    filename: str | None = None


class ValidationLocation(BaseModel):
    path: str
    line: int | None = None


class ValidationErrorItem(BaseModel):
    code: str
    message: str
    location: str | None = None


class SpecValidationReport(BaseModel):
    valid: bool
    spec_kind: str | None = None
    operation_count: int = 0
    errors: list[ValidationErrorItem] = Field(default_factory=list)


class SpecVersionResponse(BaseModel):
    id: str
    project_id: str
    version_no: int
    source_type: str
    source_ref: str | None = None
    format: str
    spec_kind: str
    sha256: str
    operation_count: int
    created_at: str
    raw_text: str | None = None


# --- Operations ---


class OperationItemResponse(BaseModel):
    operation_key: str
    method: str
    path: str
    summary: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    deprecated: bool = False
    risk: Literal["read", "write", "destructive"]
    enabled: bool
    skipped: bool = False
    skipped_reason: str | None = None
    tool_name: str
    annotations: dict[str, Any] = Field(default_factory=dict)
    group: str | None = None


class OperationsListResponse(BaseModel):
    total_count: int
    enabled_count: int
    read_count: int
    write_count: int
    destructive_count: int
    operations: list[OperationItemResponse]


class OperationUpdateItem(BaseModel):
    operation_key: str
    enabled: bool | None = None
    tool_name_override: str | None = None
    description_override: str | None = None
    group_override: str | None = None


class OperationsBulkUpdateRequest(BaseModel):
    operations: list[OperationUpdateItem]


class OperationsPresetRequest(BaseModel):
    preset: Literal["read-only", "all", "none", "by-tag"]
    tags: list[str] | None = None


# --- Settings ---


class ProjectSettingsResponse(BaseModel):
    project_id: str
    base_url: str | None = None
    timeout_s: int = 30
    max_response_chars: int = 20000
    retry_safe_requests: bool = True
    max_retries: int = 2
    naming_style: str = "snake"
    include_writes_default: bool = False
    auth_mapping: dict[str, Any] = Field(default_factory=dict)
    transports: list[str] = Field(default_factory=lambda: ["stdio", "streamable-http"])
    tool_prefix: str | None = None


class ProjectSettingsUpdateRequest(BaseModel):
    base_url: str | None = None
    timeout_s: int | None = Field(default=None, ge=1, le=300)
    max_response_chars: int | None = Field(default=None, ge=100, le=500000)
    retry_safe_requests: bool | None = None
    max_retries: int | None = Field(default=None, ge=0, le=10)
    naming_style: str | None = None
    include_writes_default: bool | None = None
    auth_mapping: dict[str, Any] | None = None
    transports: list[str] | None = None
    tool_prefix: str | None = None


# --- Review ---


class ReviewFindingItem(BaseModel):
    id: str | None = None
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    location: str | None = None
    suggestion: str | None = None
    operation_key: str | None = None
    acknowledged: bool = False


class ReviewResponse(BaseModel):
    has_blocking_errors: bool
    total_findings: int
    error_count: int
    warning_count: int
    info_count: int
    findings: list[ReviewFindingItem]


class ReviewAcknowledgeRequest(BaseModel):
    finding_codes: list[str] = Field(default_factory=list)
    spec_version_id: str | None = Field(
        default=None, description="Optional spec version to scope acknowledgements to"
    )


# --- Builds ---


class BuildSummaryResponse(BaseModel):
    id: str
    project_id: str
    spec_version_id: str
    build_no: int
    status: str
    tool_count: int
    warning_count: int
    artifact_sha256: str | None = None
    error_message: str | None = None
    created_at: str


class FileTreeNode(BaseModel):
    name: str
    path: str
    type: Literal["file", "directory"]
    size: int | None = None
    children: list["FileTreeNode"] | None = None


class FileContentResponse(BaseModel):
    path: str
    content: str
    size: int


# --- Auth (Exposed Mode) ---


class LoginRequest(BaseModel):
    token: str


class LoginResponse(BaseModel):
    status: str
    message: str
