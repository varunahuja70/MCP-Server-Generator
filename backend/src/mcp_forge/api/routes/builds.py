"""Builds and artifacts REST API endpoints: trigger build, list, file tree, file content, download, connect snippets."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from mcp_forge.api.deps import get_db, require_auth
from mcp_forge.api.schemas.models import (
    BuildSummaryResponse,
    FileContentResponse,
)
from mcp_forge.db.models.build import Build
from mcp_forge.db.models.project import Project
from mcp_forge.errors import NotFoundError
from mcp_forge.services.builds import (
    create_build_for_project,
    generate_client_snippets,
    get_build_file_content,
    list_build_file_tree,
)

# Project builds router
project_builds_router = APIRouter(
    prefix="/api/projects/{project_id}/builds",
    tags=["Builds"],
    dependencies=[Depends(require_auth)],
)

# Standalone builds router for build-specific operations
builds_router = APIRouter(
    prefix="/api/builds", tags=["Builds"], dependencies=[Depends(require_auth)]
)


@project_builds_router.post("", response_model=BuildSummaryResponse)
async def trigger_build(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger a new build for the project."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    build_res = await create_build_for_project(session=db, project_id=project_id)
    return {
        "id": build_res.id,
        "project_id": build_res.project_id,
        "spec_version_id": build_res.spec_version_id,
        "build_no": build_res.build_no,
        "status": build_res.status,
        "tool_count": build_res.tool_count,
        "warning_count": build_res.warning_count,
        "artifact_sha256": build_res.artifact_sha256,
        "error_message": build_res.error_message_safe,
        "created_at": build_res.created_at,
    }


@project_builds_router.get("", response_model=list[BuildSummaryResponse])
async def list_project_builds(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all builds for a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    stmt = select(Build).where(Build.project_id == project_id).order_by(Build.build_no.desc())
    res = await db.execute(stmt)
    builds = res.scalars().all()

    return [
        {
            "id": b.id,
            "project_id": b.project_id,
            "spec_version_id": b.spec_version_id,
            "build_no": b.build_no,
            "status": b.status,
            "tool_count": b.tool_count,
            "warning_count": b.warning_count,
            "artifact_sha256": b.artifact_sha256,
            "error_message": b.error_message_safe,
            "created_at": b.created_at,
        }
        for b in builds
    ]


@builds_router.get("/{build_id}", response_model=BuildSummaryResponse)
async def get_build_summary(
    build_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get single build metadata."""
    build = await db.get(Build, build_id)
    if not build:
        raise NotFoundError(f"Build with ID '{build_id}' not found.")

    return {
        "id": build.id,
        "project_id": build.project_id,
        "spec_version_id": build.spec_version_id,
        "build_no": build.build_no,
        "status": build.status,
        "tool_count": build.tool_count,
        "warning_count": build.warning_count,
        "artifact_sha256": build.artifact_sha256,
        "error_message": build.error_message_safe,
        "created_at": build.created_at,
    }


@builds_router.get("/{build_id}/files")
async def get_files_tree(
    build_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Get hierarchical file tree of generated project."""
    build = await db.get(Build, build_id)
    if not build or not build.artifact_path:
        raise NotFoundError(f"Build with ID '{build_id}' not found.")

    server_dir = Path(build.artifact_path).parent / f"{Path(build.artifact_path).stem}"
    if not server_dir.exists():
        server_dir = Path(build.artifact_path).parent / "server"

    tree = list_build_file_tree(server_dir)
    return tree


@builds_router.get("/{build_id}/files/content", response_model=FileContentResponse)
async def get_file_content(
    build_id: str,
    path: str = Query(..., description="Relative file path within generated project"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve text content of a generated project file safely."""
    build = await db.get(Build, build_id)
    if not build or not build.artifact_path:
        raise NotFoundError(f"Build with ID '{build_id}' not found.")

    server_dir = Path(build.artifact_path).parent / f"{Path(build.artifact_path).stem}"
    if not server_dir.exists():
        server_dir = Path(build.artifact_path).parent / "server"

    content = get_build_file_content(server_dir, path)
    return {
        "path": path,
        "content": content,
        "size": len(content.encode("utf-8")),
    }


@builds_router.get("/{build_id}/download")
async def download_build_archive(
    build_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download the deterministic ZIP artifact for a build."""
    build = await db.get(Build, build_id)
    if not build:
        raise NotFoundError(f"Build with ID '{build_id}' not found.")

    if not build.artifact_path:
        raise NotFoundError(f"No artifact package found for build '{build_id}'.")

    artifact_file = Path(build.artifact_path)
    if not artifact_file.exists():
        raise NotFoundError("Build artifact file missing on disk.")

    return FileResponse(
        path=artifact_file,
        filename=artifact_file.name,
        media_type="application/zip",
    )


@builds_router.get("/{build_id}/connect")
async def get_connect_snippets(
    build_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get ready-to-copy client configuration snippets (Claude Desktop, Cursor, stdio, HTTP)."""
    stmt = select(Build).where(Build.id == build_id).options(joinedload(Build.project))
    res = await db.execute(stmt)
    build = res.scalar_one_or_none()
    if not build or not build.artifact_path:
        raise NotFoundError(f"Build with ID '{build_id}' not found.")

    server_dir = Path(build.artifact_path).parent / "server"
    snippets = generate_client_snippets(
        project_slug=build.project.slug,
        server_dir=server_dir,
    )
    return snippets
