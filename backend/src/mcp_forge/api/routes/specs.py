"""Specs REST API endpoints: upload, paste, URL import, list, detail, and diff."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.api.deps import get_current_settings, get_db, require_auth
from mcp_forge.api.schemas.models import (
    SpecCreateRequest,
    SpecVersionResponse,
)
from mcp_forge.config import Settings
from mcp_forge.core.diff import SpecDiffReport, diff_spec_texts
from mcp_forge.core.ingest import ingest_from_text, ingest_from_url
from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.selection import determine_default_selection
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.db.models.operation_config import OperationConfig
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.errors import NotFoundError, ValidationError

router = APIRouter(
    prefix="/api/projects/{project_id}/specs", tags=["Specs"], dependencies=[Depends(require_auth)]
)


@router.post("", response_model=SpecVersionResponse)
async def create_spec_version(
    project_id: str,
    body: SpecCreateRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_current_settings),
) -> dict[str, Any]:
    """Ingest a new specification version (via upload, paste, or link), preserving matching operation selections."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    source_ref = body.filename

    # Ingest text based on source_type
    if body.source_type == "link":
        if not body.url:
            raise ValidationError("URL must be provided when source_type='link'.")
        source_ref = body.url
        ingest_res = await ingest_from_url(
            url=body.url,
            allow_private=settings.allow_private_spec_urls,
            max_bytes=settings.max_spec_bytes,
        )
    elif body.source_type in ("paste", "upload"):
        if not body.content:
            raise ValidationError(
                f"Content must be provided when source_type='{body.source_type}'."
            )
        ref_name = (
            body.filename or "uploaded-spec" if body.source_type == "upload" else "pasted-spec"
        )
        ingest_res = ingest_from_text(body.content, source_ref=ref_name)
    else:
        raise ValidationError(f"Unsupported source_type: '{body.source_type}'.")

    # Parse & validate OpenAPI / Swagger
    parsed = parse_and_validate(ingest_res.raw_text, allow_remote_refs=settings.allow_remote_refs)
    ir = normalize_spec(parsed)

    # Calculate next version number
    stmt_v = select(func.coalesce(func.max(SpecVersion.version_no), 0)).where(
        SpecVersion.project_id == project_id
    )
    res_v = await db.execute(stmt_v)
    next_ver = res_v.scalar_one() + 1

    spec_version = SpecVersion(
        project_id=project_id,
        version_no=next_ver,
        source_type=body.source_type,
        source_ref=source_ref,
        format=ingest_res.format,
        spec_kind=parsed.kind,
        sha256=ingest_res.sha256,
        raw_text=ingest_res.raw_text,
        operation_count=len(ir.operations),
    )
    db.add(spec_version)
    await db.flush()

    # Preserve or initialize operation configurations
    # Existing operation configs
    stmt_ops = select(OperationConfig).where(OperationConfig.project_id == project_id)
    res_ops = await db.execute(stmt_ops)
    existing_ops = {op.operation_key: op for op in res_ops.scalars().all()}

    # Populate any new operations that don't already have an OperationConfig row
    for op in ir.operations:
        if op.operation_key not in existing_ops:
            def_enabled, _, _ = determine_default_selection(op)
            new_op_cfg = OperationConfig(
                project_id=project_id,
                operation_key=op.operation_key,
                enabled=def_enabled,
            )
            db.add(new_op_cfg)

    # Update project base_url if not set and servers present
    proj_settings = await db.get(ProjectSettings, project_id)
    if proj_settings and not proj_settings.base_url and ir.servers:
        proj_settings.base_url = ir.servers[0].url

    await db.commit()
    await db.refresh(spec_version)

    return {
        "id": spec_version.id,
        "project_id": spec_version.project_id,
        "version_no": spec_version.version_no,
        "source_type": spec_version.source_type,
        "source_ref": spec_version.source_ref,
        "format": spec_version.format,
        "spec_kind": spec_version.spec_kind,
        "sha256": spec_version.sha256,
        "operation_count": spec_version.operation_count,
        "created_at": spec_version.created_at,
    }


@router.get("", response_model=list[SpecVersionResponse])
async def list_spec_versions(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all specification versions for a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    stmt = (
        select(SpecVersion)
        .where(SpecVersion.project_id == project_id)
        .order_by(SpecVersion.version_no.desc())
    )
    res = await db.execute(stmt)
    versions = res.scalars().all()

    return [
        {
            "id": v.id,
            "project_id": v.project_id,
            "version_no": v.version_no,
            "source_type": v.source_type,
            "source_ref": v.source_ref,
            "format": v.format,
            "spec_kind": v.spec_kind,
            "sha256": v.sha256,
            "operation_count": v.operation_count,
            "created_at": v.created_at,
        }
        for v in versions
    ]


@router.get("/{vid}", response_model=SpecVersionResponse)
async def get_spec_version(
    project_id: str,
    vid: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a specific spec version including raw text."""
    stmt = select(SpecVersion).where(
        SpecVersion.project_id == project_id,
        (SpecVersion.id == vid) | (SpecVersion.version_no == int(vid) if vid.isdigit() else False),
    )
    res = await db.execute(stmt)
    v = res.scalar_one_or_none()
    if not v:
        raise NotFoundError(f"Spec version '{vid}' not found for project '{project_id}'.")

    return {
        "id": v.id,
        "project_id": v.project_id,
        "version_no": v.version_no,
        "source_type": v.source_type,
        "source_ref": v.source_ref,
        "format": v.format,
        "spec_kind": v.spec_kind,
        "sha256": v.sha256,
        "operation_count": v.operation_count,
        "created_at": v.created_at,
        "raw_text": v.raw_text,
    }


@router.get("/{vid}/diff", response_model=SpecDiffReport)
async def diff_spec_version(
    project_id: str,
    vid: str,
    against: str = Query(..., description="Target version ID or version number to diff against"),
    db: AsyncSession = Depends(get_db),
) -> SpecDiffReport:
    """Compare this spec version against another version."""
    stmt_v1 = select(SpecVersion).where(
        SpecVersion.project_id == project_id,
        (SpecVersion.id == vid) | (SpecVersion.version_no == int(vid) if vid.isdigit() else False),
    )
    res_v1 = await db.execute(stmt_v1)
    v1 = res_v1.scalar_one_or_none()
    if not v1:
        raise NotFoundError(f"Base spec version '{vid}' not found.")

    stmt_v2 = select(SpecVersion).where(
        SpecVersion.project_id == project_id,
        (SpecVersion.id == against)
        | (SpecVersion.version_no == int(against) if against.isdigit() else False),
    )
    res_v2 = await db.execute(stmt_v2)
    v2 = res_v2.scalar_one_or_none()
    if not v2:
        raise NotFoundError(f"Comparison spec version '{against}' not found.")

    report = diff_spec_texts(
        base_text=v1.raw_text,
        target_text=v2.raw_text,
        base_version_no=v1.version_no,
        target_version_no=v2.version_no,
    )
    return report
