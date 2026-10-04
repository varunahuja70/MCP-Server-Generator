"""Projects REST API endpoints for creation, listing, updating, and deletion."""

import re
import shutil
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mcp_forge.api.deps import get_current_settings, get_db, require_auth
from mcp_forge.api.schemas.models import (
    ProjectCreateRequest,
    ProjectDeleteRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from mcp_forge.config import Settings
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.errors import ConflictError, NotFoundError, ValidationError

router = APIRouter(prefix="/api/projects", tags=["Projects"], dependencies=[Depends(require_auth)])


def slugify(text: str) -> str:
    """Generate safe lower snake_case/kebab slug."""
    s = re.sub(r"[^a-zA-Z0-9_-]", "-", text.strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "project"
    return s[:64]


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all projects with metadata, latest build status, and operation counts."""
    stmt = (
        select(Project)
        .options(
            selectinload(Project.specs),
            selectinload(Project.builds),
        )
        .order_by(Project.created_at.desc())
    )
    res = await db.execute(stmt)
    projects = res.scalars().all()

    output = []
    for p in projects:
        latest_spec = p.specs[0] if p.specs else None
        latest_build = p.builds[0] if p.builds else None
        output.append(
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "archived_at": p.archived_at,
                "operation_count": latest_spec.operation_count if latest_spec else 0,
                "latest_build_status": latest_build.status if latest_build else None,
                "spec_version_count": len(p.specs),
            }
        )
    return output


@router.post("", response_model=ProjectResponse)
async def create_project(
    body: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Create a new empty project."""
    slug_val = body.slug or slugify(body.name)
    slug_val = slugify(slug_val)

    # Check slug collision
    stmt = select(Project).where(Project.slug == slug_val)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ConflictError(f"A project with slug '{slug_val}' already exists.")

    project = Project(name=body.name.strip(), slug=slug_val)
    db.add(project)
    await db.flush()

    # Create default project settings
    settings = ProjectSettings(project_id=project.id)
    db.add(settings)
    await db.commit()
    await db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "slug": project.slug,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "archived_at": project.archived_at,
        "operation_count": 0,
        "latest_build_status": None,
        "spec_version_count": 0,
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get project details by ID."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.specs),
            selectinload(Project.builds),
        )
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    latest_spec = project.specs[0] if project.specs else None
    latest_build = project.builds[0] if project.builds else None

    return {
        "id": project.id,
        "name": project.name,
        "slug": project.slug,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "archived_at": project.archived_at,
        "operation_count": latest_spec.operation_count if latest_spec else 0,
        "latest_build_status": latest_build.status if latest_build else None,
        "spec_version_count": len(project.specs),
    }


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: ProjectUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update project name or slug."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.specs),
            selectinload(Project.builds),
        )
    )
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    if body.name is not None:
        project.name = body.name.strip()

    if body.slug is not None:
        new_slug = slugify(body.slug)
        if new_slug != project.slug:
            chk_stmt = select(Project).where(Project.slug == new_slug)
            chk_res = await db.execute(chk_stmt)
            if chk_res.scalar_one_or_none():
                raise ConflictError(f"Slug '{new_slug}' is already taken.")
            project.slug = new_slug

    await db.commit()
    await db.refresh(project)

    latest_spec = project.specs[0] if project.specs else None
    latest_build = project.builds[0] if project.builds else None

    return {
        "id": project.id,
        "name": project.name,
        "slug": project.slug,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "archived_at": project.archived_at,
        "operation_count": latest_spec.operation_count if latest_spec else 0,
        "latest_build_status": latest_build.status if latest_build else None,
        "spec_version_count": len(project.specs),
    }


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    body: ProjectDeleteRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_current_settings),
) -> dict[str, Any]:
    """Delete project with confirmation body checking slug."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    if body.confirm_slug != project.slug:
        raise ValidationError(
            f"Confirmation slug '{body.confirm_slug}' does not match project slug '{project.slug}'.",
            details={"expected": project.slug, "provided": body.confirm_slug},
        )

    # Clean up project build artifacts on disk if they exist
    builds_dir = settings.forge_data_dir / "builds" / project.slug
    if builds_dir.exists():
        shutil.rmtree(builds_dir, ignore_errors=True)

    project_dir = settings.forge_data_dir / "projects" / project.slug
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)

    await db.delete(project)
    await db.commit()

    return {"status": "deleted", "project_id": project_id, "slug": project.slug}
