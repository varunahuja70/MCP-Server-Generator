"""Spec review and findings persistence service."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.mapping.mapper import map_api_to_toolset
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.core.review.engine import review_api
from mcp_forge.core.review.models import ReviewReport
from mcp_forge.db.models.operation_config import OperationConfig
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.review_finding import ReviewFinding as ReviewFindingModel
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.errors import NotFoundError


async def run_spec_review(
    session: AsyncSession,
    project_id: str,
    spec_version_id: str,
    build_id: str | None = None,
) -> ReviewReport:
    """Execute review engine against spec version, associate findings with project/version/build, and return report."""
    # Verify project exists
    project = await session.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    # Get spec version
    spec_version = await session.get(SpecVersion, spec_version_id)
    if not spec_version:
        raise NotFoundError(f"SpecVersion with ID '{spec_version_id}' not found.")

    # Get project settings if any
    settings = await session.get(ProjectSettings, project_id)
    tool_prefix = settings.tool_prefix if settings else None

    # Get user operation overrides if any
    stmt_ops = select(OperationConfig).where(OperationConfig.project_id == project_id)
    res_ops = await session.execute(stmt_ops)
    op_configs = res_ops.scalars().all()

    name_overrides = {
        op.operation_key: op.tool_name_override for op in op_configs if op.tool_name_override
    }
    desc_overrides = {
        op.operation_key: op.description_override for op in op_configs if op.description_override
    }
    enabled_overrides = {op.operation_key: op.enabled for op in op_configs}

    # Fetch previously acknowledged findings
    stmt_ack = select(ReviewFindingModel).where(
        ReviewFindingModel.project_id == project_id,
        ReviewFindingModel.spec_version_id == spec_version_id,
        ReviewFindingModel.acknowledged.is_(True),
    )
    res_ack = await session.execute(stmt_ack)
    ack_findings = res_ack.scalars().all()
    ack_set = {(f.code, f.operation_key) for f in ack_findings}

    # Parse and normalize spec
    parsed = parse_and_validate(spec_version.raw_text)
    ir = normalize_spec(parsed)

    toolset = map_api_to_toolset(
        ir=ir,
        tool_prefix=tool_prefix,
        name_overrides=name_overrides,
        description_overrides=desc_overrides,
        enabled_overrides=enabled_overrides,
    )

    report = review_api(
        ir=ir,
        toolset=toolset,
        raw_text=spec_version.raw_text,
        raw_spec_dict=parsed.raw_dict,
        acknowledged_findings=ack_set,
    )

    # Clean existing non-acknowledged findings for this spec version if no build_id, or associate with build_id
    if build_id:
        # Save snapshot of findings for this build
        for f in report.findings:
            db_finding = ReviewFindingModel(
                project_id=project_id,
                spec_version_id=spec_version_id,
                build_id=build_id,
                severity=f.severity,
                code=f.code,
                message=f.message,
                operation_key=f.operation_key,
                suggestion=f.suggestion,
                acknowledged=f.acknowledged,
            )
            session.add(db_finding)
    else:
        # Standalone review refresh: remove previous unacknowledged findings
        await session.execute(
            delete(ReviewFindingModel).where(
                ReviewFindingModel.project_id == project_id,
                ReviewFindingModel.spec_version_id == spec_version_id,
                ReviewFindingModel.build_id.is_(None),
                ReviewFindingModel.acknowledged.is_(False),
            )
        )
        for f in report.findings:
            if not f.acknowledged:
                db_finding = ReviewFindingModel(
                    project_id=project_id,
                    spec_version_id=spec_version_id,
                    build_id=None,
                    severity=f.severity,
                    code=f.code,
                    message=f.message,
                    operation_key=f.operation_key,
                    suggestion=f.suggestion,
                    acknowledged=False,
                )
                session.add(db_finding)

    await session.flush()
    return report
