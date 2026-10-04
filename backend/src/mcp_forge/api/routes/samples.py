"""Samples discovery and project creation from sample."""

import hashlib
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.api.deps import get_db, require_auth
from mcp_forge.api.schemas.models import (
    ProjectFromSampleRequest,
    ProjectResponse,
    SampleSummary,
)
from mcp_forge.core.ir import normalize_spec
from mcp_forge.core.parse import parse_and_validate
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.db.models.spec_version import SpecVersion
from mcp_forge.errors import NotFoundError

router = APIRouter(prefix="/api/samples", tags=["Samples"], dependencies=[Depends(require_auth)])

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "samples"

KNOWN_SAMPLES = [
    {
        "id": "bookshop",
        "title": "Bookshop API",
        "description": "REST API for a bookstore with books, orders, authors, and reviews. OpenAPI 3.0.",
        "filename": "bookshop.openapi.yaml",
        "format": "yaml",
    },
    {
        "id": "tasks",
        "title": "Task Management API",
        "description": "Task and project management API with CRUD operations and filtering. OpenAPI 3.0.",
        "filename": "tasks.openapi.json",
        "format": "json",
    },
    {
        "id": "legacy",
        "title": "Legacy Swagger API",
        "description": "Petstore-style API specified in Swagger 2.0 (OpenAPI 2.0).",
        "filename": "legacy-swagger2.json",
        "format": "json",
    },
]


@router.get("", response_model=list[SampleSummary])
async def list_samples() -> list[dict[str, Any]]:
    """List bundled sample OpenAPI/Swagger specifications."""
    results = []
    for s in KNOWN_SAMPLES:
        file_path = SAMPLES_DIR / s["filename"]
        op_count = 0
        if file_path.exists():
            try:
                raw = file_path.read_text(encoding="utf-8")
                parsed = parse_and_validate(raw)
                ir = normalize_spec(parsed)
                op_count = len(ir.operations)
            except Exception:
                op_count = 0

        results.append(
            {
                "id": s["id"],
                "title": s["title"],
                "description": s["description"],
                "filename": s["filename"],
                "format": s["format"],
                "operation_count": op_count,
            }
        )
    return results


@router.post("/create-project", response_model=ProjectResponse)
async def create_project_from_sample(
    body: ProjectFromSampleRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new project pre-populated with a bundled sample API."""
    sample_info = next((s for s in KNOWN_SAMPLES if s["id"] == body.sample_id), None)
    if not sample_info:
        raise NotFoundError(f"Sample with ID '{body.sample_id}' not found.")

    file_path = SAMPLES_DIR / sample_info["filename"]
    if not file_path.exists():
        raise NotFoundError(f"Sample file '{sample_info['filename']}' not found on disk.")

    raw_text = file_path.read_text(encoding="utf-8")
    parsed = parse_and_validate(raw_text)
    ir = normalize_spec(parsed)

    proj_name = body.name or sample_info["title"]
    proj_slug = body.slug or f"{body.sample_id}-sample"

    # Ensure slug uniqueness
    stmt = select(Project).where(Project.slug == proj_slug)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        # append numeric suffix
        suffix = 2
        while True:
            candidate = f"{proj_slug}-{suffix}"
            stmt2 = select(Project).where(Project.slug == candidate)
            res2 = await db.execute(stmt2)
            if not res2.scalar_one_or_none():
                proj_slug = candidate
                break
            suffix += 1

    project = Project(name=proj_name, slug=proj_slug)
    db.add(project)
    await db.flush()

    # Settings
    base_url = ir.servers[0].url if ir.servers else "http://127.0.0.1:8000"
    settings = ProjectSettings(project_id=project.id, base_url=base_url)
    db.add(settings)

    # SpecVersion
    sha256 = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    spec_ver = SpecVersion(
        project_id=project.id,
        version_no=1,
        source_type="sample",
        source_ref=sample_info["filename"],
        format=sample_info["format"],
        spec_kind=parsed.kind,
        sha256=sha256,
        raw_text=raw_text,
        operation_count=len(ir.operations),
    )
    db.add(spec_ver)
    await db.commit()
    await db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "slug": project.slug,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "archived_at": project.archived_at,
        "operation_count": len(ir.operations),
        "latest_build_status": None,
        "spec_version_count": 1,
    }
