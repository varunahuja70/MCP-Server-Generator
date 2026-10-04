"""Operations REST API endpoints: list with risk/selection, bulk update, and presets."""

from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.api.deps import get_db, require_auth
from mcp_forge.api.schemas.models import (
    OperationsBulkUpdateRequest,
    OperationsListResponse,
    OperationsPresetRequest,
)
from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.annotations import get_tool_annotations
from mcp_forge.core.mapping.selection import determine_default_selection, is_read_only_method
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.core.security.identifiers import is_valid_identifier, sanitize_identifier
from mcp_forge.db.models.operation_config import OperationConfig
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.errors import NotFoundError, ValidationError

router = APIRouter(
    prefix="/api/projects/{project_id}/operations",
    tags=["Operations"],
    dependencies=[Depends(require_auth)],
)


def method_to_risk(method: str) -> Literal["read", "write", "destructive"]:
    """Categorize HTTP method into risk level."""
    m = method.upper()
    if m in ("GET", "HEAD"):
        return "read"
    if m == "DELETE":
        return "destructive"
    return "write"


@router.get("", response_model=OperationsListResponse)
async def list_operations(
    project_id: str,
    tag: str | None = Query(default=None),
    method: str | None = Query(default=None),
    risk: str | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List operations with current selection, risk labels, and user overrides."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    # Get latest spec version
    stmt_spec = (
        select(SpecVersion)
        .where(SpecVersion.project_id == project_id)
        .order_by(SpecVersion.version_no.desc())
        .limit(1)
    )
    res_spec = await db.execute(stmt_spec)
    spec_ver = res_spec.scalar_one_or_none()

    if not spec_ver:
        return {
            "total_count": 0,
            "enabled_count": 0,
            "read_count": 0,
            "write_count": 0,
            "destructive_count": 0,
            "operations": [],
        }

    parsed = parse_and_validate(spec_ver.raw_text)
    ir = normalize_spec(parsed)

    # Fetch existing operation configs
    stmt_cfg = select(OperationConfig).where(OperationConfig.project_id == project_id)
    res_cfg = await db.execute(stmt_cfg)
    cfg_map = {c.operation_key: c for c in res_cfg.scalars().all()}

    settings = await db.get(ProjectSettings, project_id)
    prefix = settings.tool_prefix if settings else None

    items: list[dict[str, Any]] = []
    read_c = write_c = dest_c = enabled_c = 0

    for op in ir.operations:
        r_level = method_to_risk(op.method)
        if r_level == "read":
            read_c += 1
        elif r_level == "destructive":
            dest_c += 1
        else:
            write_c += 1

        cfg = cfg_map.get(op.operation_key)
        def_enabled, skipped, skipped_reason = determine_default_selection(op)
        is_enabled = cfg.enabled if cfg else def_enabled

        if is_enabled:
            enabled_c += 1

        # Tool name calculation
        if cfg and cfg.tool_name_override:
            tool_name = cfg.tool_name_override
        else:
            base_ident = op.operation_id or f"{op.method}_{op.path}"
            tool_name = sanitize_identifier(base_ident, prefix=prefix or "tool")

        annotations = get_tool_annotations(op.method, title=op.summary)

        # Apply filters
        if tag and tag not in op.tags:
            continue
        if method and op.method.upper() != method.upper():
            continue
        if risk and r_level != risk:
            continue
        if enabled is not None and is_enabled != enabled:
            continue
        if search:
            s_low = search.lower()
            text_haystack = (
                f"{op.operation_key} {op.path} {op.summary or ''} {op.description or ''}".lower()
            )
            if s_low not in text_haystack:
                continue

        items.append(
            {
                "operation_key": op.operation_key,
                "method": op.method,
                "path": op.path,
                "summary": op.summary,
                "description": cfg.description_override
                if (cfg and cfg.description_override)
                else op.description,
                "tags": op.tags,
                "deprecated": op.deprecated,
                "risk": r_level,
                "enabled": is_enabled,
                "skipped": skipped,
                "skipped_reason": skipped_reason,
                "tool_name": tool_name,
                "annotations": annotations,
                "group": cfg.group_override
                if (cfg and cfg.group_override)
                else (op.tags[0] if op.tags else None),
            }
        )

    return {
        "total_count": len(ir.operations),
        "enabled_count": enabled_c,
        "read_count": read_c,
        "write_count": write_c,
        "destructive_count": dest_c,
        "operations": items,
    }


@router.put("")
async def bulk_update_operations(
    project_id: str,
    body: OperationsBulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Bulk update operation enabled state, tool names, descriptions, or groups."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    stmt_cfg = select(OperationConfig).where(OperationConfig.project_id == project_id)
    res_cfg = await db.execute(stmt_cfg)
    cfg_map = {c.operation_key: c for c in res_cfg.scalars().all()}

    updated_count = 0
    for item in body.operations:
        # Validate tool name override if supplied
        if item.tool_name_override:
            if not is_valid_identifier(item.tool_name_override):
                raise ValidationError(
                    f"Tool name '{item.tool_name_override}' does not match identifier pattern '^[a-z][a-z0-9_]{{0,63}}$'.",
                    details={"tool_name": item.tool_name_override},
                )

        cfg = cfg_map.get(item.operation_key)
        if not cfg:
            cfg = OperationConfig(
                project_id=project_id,
                operation_key=item.operation_key,
                enabled=item.enabled if item.enabled is not None else False,
                tool_name_override=item.tool_name_override,
                description_override=item.description_override,
                group_override=item.group_override,
            )
            db.add(cfg)
            cfg_map[item.operation_key] = cfg
        else:
            if item.enabled is not None:
                cfg.enabled = item.enabled
            if item.tool_name_override is not None:
                cfg.tool_name_override = item.tool_name_override or None
            if item.description_override is not None:
                cfg.description_override = item.description_override or None
            if item.group_override is not None:
                cfg.group_override = item.group_override or None

        updated_count += 1

    await db.commit()
    return {"status": "updated", "updated_count": updated_count}


@router.post("/preset")
async def apply_operations_preset(
    project_id: str,
    body: OperationsPresetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Apply selection preset across all operations (read-only, all, none, by-tag)."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    stmt_spec = (
        select(SpecVersion)
        .where(SpecVersion.project_id == project_id)
        .order_by(SpecVersion.version_no.desc())
        .limit(1)
    )
    res_spec = await db.execute(stmt_spec)
    spec_ver = res_spec.scalar_one_or_none()
    if not spec_ver:
        raise NotFoundError("No specification versions exist for this project.")

    parsed = parse_and_validate(spec_ver.raw_text)
    ir = normalize_spec(parsed)

    stmt_cfg = select(OperationConfig).where(OperationConfig.project_id == project_id)
    res_cfg = await db.execute(stmt_cfg)
    cfg_map = {c.operation_key: c for c in res_cfg.scalars().all()}

    selected_count = 0
    filter_tags = set(body.tags or [])

    for op in ir.operations:
        cfg = cfg_map.get(op.operation_key)
        if not cfg:
            cfg = OperationConfig(project_id=project_id, operation_key=op.operation_key)
            db.add(cfg)
            cfg_map[op.operation_key] = cfg

        if op.unsupported_reason:
            cfg.enabled = False
            continue

        if body.preset == "read-only":
            cfg.enabled = is_read_only_method(op.method) and not op.deprecated
        elif body.preset == "all":
            cfg.enabled = True
        elif body.preset == "none":
            cfg.enabled = False
        elif body.preset == "by-tag":
            cfg.enabled = bool(set(op.tags) & filter_tags)

        if cfg.enabled:
            selected_count += 1

    await db.commit()
    return {"status": "preset_applied", "preset": body.preset, "enabled_count": selected_count}
