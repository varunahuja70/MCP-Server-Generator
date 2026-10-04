"""Review REST API endpoints: trigger review findings and acknowledge blocking findings."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.api.deps import get_db, require_auth
from mcp_forge.api.schemas.models import (
    ReviewAcknowledgeRequest,
    ReviewResponse,
)
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.review_finding import ReviewFinding as ReviewFindingModel
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.errors import NotFoundError
from mcp_forge.services.review import run_spec_review

router = APIRouter(
    prefix="/api/projects/{project_id}/review",
    tags=["Review"],
    dependencies=[Depends(require_auth)],
)


@router.post("", response_model=ReviewResponse)
async def review_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run review engine on the latest spec version and persist findings."""
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

    report = await run_spec_review(session=db, project_id=project_id, spec_version_id=spec_ver.id)

    # Fetch updated persisted findings
    stmt_f = select(ReviewFindingModel).where(
        ReviewFindingModel.project_id == project_id,
        ReviewFindingModel.spec_version_id == spec_ver.id,
    )
    res_f = await db.execute(stmt_f)
    findings = res_f.scalars().all()

    err_c = sum(1 for f in findings if f.severity == "error")
    warn_c = sum(1 for f in findings if f.severity == "warning")
    info_c = sum(1 for f in findings if f.severity == "info")

    return {
        "has_blocking_errors": report.has_blocking_errors,
        "total_findings": len(findings),
        "error_count": err_c,
        "warning_count": warn_c,
        "info_count": info_c,
        "findings": [
            {
                "id": f.id,
                "code": f.code,
                "severity": f.severity,
                "message": f.message,
                "suggestion": f.suggestion,
                "operation_key": f.operation_key,
                "acknowledged": f.acknowledged,
            }
            for f in findings
        ],
    }


@router.post("/acknowledge")
async def acknowledge_findings(
    project_id: str,
    body: ReviewAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Acknowledge blocking error findings so that generation may proceed."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    stmt = select(ReviewFindingModel).where(
        ReviewFindingModel.project_id == project_id,
        ReviewFindingModel.code.in_(body.finding_codes),
    )
    res = await db.execute(stmt)
    findings = res.scalars().all()

    for f in findings:
        f.acknowledged = True

    await db.commit()
    return {"status": "acknowledged", "acknowledged_count": len(findings)}
