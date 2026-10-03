"""Manifest (tools.json) document model, JSON Schema validation, and ToolSet container."""

from typing import Any

import jsonschema
from pydantic import BaseModel, ConfigDict, Field

from mcp_forge.core.security.identifiers import IDENTIFIER_REGEX
from mcp_forge.errors import InvalidSpecError

TOOLS_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "info", "auth", "tools"],
    "properties": {
        "schema_version": {"type": "string"},
        "info": {
            "type": "object",
            "required": ["title", "version"],
            "properties": {
                "title": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": ["string", "null"]},
                "base_url": {"type": "string"},
                "generator_version": {"type": "string"},
            },
        },
        "auth": {"type": "object"},
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "name",
                    "operation_key",
                    "method",
                    "path",
                    "description",
                    "input_schema",
                    "param_locations",
                ],
                "properties": {
                    "name": {
                        "type": "string",
                        "pattern": "^[a-z][a-z0-9_]{0,63}$",
                    },
                    "operation_key": {"type": "string"},
                    "method": {"type": "string"},
                    "path": {"type": "string"},
                    "summary": {"type": ["string", "null"]},
                    "description": {"type": "string"},
                    "input_schema": {"type": "object"},
                    "annotations": {"type": "object"},
                    "security": {"type": "array"},
                    "param_locations": {"type": "object"},
                    "is_flattened_body": {"type": "boolean"},
                },
            },
        },
    },
}


class ManifestTool(BaseModel):
    """Tool entry in tools.json."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(pattern=IDENTIFIER_REGEX.pattern)
    operation_key: str
    method: str
    path: str
    summary: str | None = None
    description: str
    input_schema: dict[str, Any]
    annotations: dict[str, Any] = Field(default_factory=dict)
    security: list[dict[str, list[str]]] = Field(default_factory=list)
    param_locations: dict[str, str] = Field(default_factory=dict)
    is_flattened_body: bool = False


# Alias ToolManifest to ManifestTool for convenience
ToolManifest = ManifestTool


class ManifestInfo(BaseModel):
    """Information block in tools.json."""

    model_config = ConfigDict(extra="ignore")

    title: str
    version: str
    description: str | None = None
    base_url: str = ""
    generator_version: str = "1.0.0"


class ManifestDoc(BaseModel):
    """Complete tools.json document model."""

    model_config = ConfigDict(extra="ignore")

    schema_version: str = "1.0"
    info: ManifestInfo
    auth: dict[str, Any] = Field(default_factory=dict)
    tools: list[ManifestTool] = Field(default_factory=list)


def validate_manifest(data: dict[str, Any]) -> None:
    """Validate tools.json data against TOOLS_JSON_SCHEMA."""
    validator = jsonschema.Draft202012Validator(TOOLS_JSON_SCHEMA)
    errors = list(validator.iter_errors(data))
    if errors:
        msg = f"tools.json schema validation failed at '{errors[0].json_path}': {errors[0].message}"
        raise InvalidSpecError(msg, details={"errors": [e.message for e in errors]})


class MappedTool(BaseModel):
    """Representation of an operation mapped into a potential tool."""

    model_config = ConfigDict(extra="ignore")

    manifest_tool: ManifestTool
    enabled: bool = False
    skipped: bool = False
    skipped_reason: str | None = None
    had_collision: bool = False
    deprecated: bool = False


class ToolSet(BaseModel):
    """Container for mapped tools with selection and manifest generation."""

    model_config = ConfigDict(extra="ignore")

    info: ManifestInfo
    auth: dict[str, Any] = Field(default_factory=dict)
    mapped_tools: list[MappedTool] = Field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.mapped_tools)

    @property
    def enabled_count(self) -> int:
        return sum(1 for t in self.mapped_tools if t.enabled and not t.skipped)

    @property
    def skipped_count(self) -> int:
        return sum(1 for t in self.mapped_tools if t.skipped)

    def to_manifest(self) -> ManifestDoc:
        """Generate ManifestDoc containing only active, enabled tools."""
        active_tools = [t.manifest_tool for t in self.mapped_tools if t.enabled and not t.skipped]
        return ManifestDoc(
            info=self.info,
            auth=self.auth,
            tools=active_tools,
        )
