"""Orchestrate conversion from IRApi to ToolSet and ManifestDoc."""

from mcp_forge.core.ir.models import IRApi
from mcp_forge.core.mapping.annotations import get_tool_annotations
from mcp_forge.core.mapping.auth import map_all_security_schemes
from mcp_forge.core.mapping.descriptions import build_tool_description
from mcp_forge.core.mapping.input_schema import build_input_schema
from mcp_forge.core.mapping.manifest import (
    ManifestInfo,
    ManifestTool,
    MappedTool,
    ToolSet,
)
from mcp_forge.core.mapping.names import resolve_tool_name
from mcp_forge.core.mapping.selection import determine_default_selection


def map_api_to_toolset(
    ir: IRApi,
    tool_prefix: str | None = None,
    name_overrides: dict[str, str] | None = None,
    description_overrides: dict[str, str] | None = None,
    enabled_overrides: dict[str, bool] | None = None,
    generator_version: str = "1.0.0",
) -> ToolSet:
    """Transform normalized IRApi into ToolSet with safe defaults."""
    name_overrides = name_overrides or {}
    description_overrides = description_overrides or {}
    enabled_overrides = enabled_overrides or {}

    base_url = ir.servers[0].url if ir.servers else ""
    auth_data = map_all_security_schemes(ir.security_schemes)

    info = ManifestInfo(
        title=ir.title,
        version=ir.version,
        description=ir.description,
        base_url=base_url,
        generator_version=generator_version,
    )

    existing_tool_names: set[str] = set()
    mapped_tools: list[MappedTool] = []

    for op in ir.operations:
        # Determine name
        had_collision = False
        if op.operation_key in name_overrides:
            tool_name = name_overrides[op.operation_key]
        else:
            tool_name, had_collision = resolve_tool_name(
                method=op.method,
                path=op.path,
                operation_id=op.operation_id,
                prefix=tool_prefix,
                existing_names=existing_tool_names,
            )
        existing_tool_names.add(tool_name)

        # Description
        if op.operation_key in description_overrides:
            description = description_overrides[op.operation_key]
        else:
            param_notes = [
                f"{p.name} ({p.in_loc}): {p.description}" for p in op.parameters if p.description
            ]
            description = build_tool_description(
                summary=op.summary,
                description=op.description,
                parameter_notes=param_notes,
            )

        # Input schema & parameter locations
        input_schema, param_locs, is_flattened = build_input_schema(op)

        # Annotations
        annotations = get_tool_annotations(op.method, title=op.summary)

        # Selection (enabled / skipped)
        def_enabled, def_skipped, def_reason = determine_default_selection(op)
        if op.operation_key in enabled_overrides:
            final_enabled = enabled_overrides[op.operation_key] and not def_skipped
        else:
            final_enabled = def_enabled

        manifest_tool = ManifestTool(
            name=tool_name,
            operation_key=op.operation_key,
            method=op.method.upper(),
            path=op.path,
            summary=op.summary,
            description=description,
            input_schema=input_schema,
            annotations=annotations,
            security=op.security,
            param_locations=param_locs,
            is_flattened_body=is_flattened,
        )

        mapped_tools.append(
            MappedTool(
                manifest_tool=manifest_tool,
                enabled=final_enabled,
                skipped=def_skipped,
                skipped_reason=def_reason,
                had_collision=had_collision,
                deprecated=op.deprecated,
            )
        )

    return ToolSet(
        info=info,
        auth=auth_data,
        mapped_tools=mapped_tools,
    )
