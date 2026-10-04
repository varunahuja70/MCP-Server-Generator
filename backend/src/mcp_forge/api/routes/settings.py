"""ProjectSettings REST API endpoints: get and update."""

import json
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_forge.api.deps import get_db, require_auth
from mcp_forge.api.schemas.models import (
    ProjectSettingsResponse,
    ProjectSettingsUpdateRequest,
)
from mcp_forge.db.models.project import Project
from mcp_forge.db.models.project_settings import ProjectSettings
from mcp_forge.errors import NotFoundError

router = APIRouter(
    prefix="/api/projects/{project_id}/settings",
    tags=["Settings"],
    dependencies=[Depends(require_auth)],
)


@router.get("", response_model=ProjectSettingsResponse)
async def get_project_settings(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve settings for a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    settings = await db.get(ProjectSettings, project_id)
    if not settings:
        settings = ProjectSettings(project_id=project_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    auth_dict = json.loads(settings.auth_mapping) if settings.auth_mapping else {}
    transports_list = (
        json.loads(settings.transports) if settings.transports else ["stdio", "streamable-http"]
    )

    return {
        "project_id": settings.project_id,
        "base_url": settings.base_url,
        "timeout_s": settings.timeout_s,
        "max_response_chars": settings.max_response_chars,
        "retry_safe_requests": settings.retry_safe_requests,
        "max_retries": settings.max_retries,
        "naming_style": settings.naming_style,
        "include_writes_default": settings.include_writes_default,
        "auth_mapping": auth_dict,
        "transports": transports_list,
        "tool_prefix": settings.tool_prefix,
    }


@router.put("", response_model=ProjectSettingsResponse)
async def update_project_settings(
    project_id: str,
    body: ProjectSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Update settings for a project."""
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError(f"Project with ID '{project_id}' not found.")

    settings = await db.get(ProjectSettings, project_id)
    if not settings:
        settings = ProjectSettings(project_id=project_id)
        db.add(settings)

    if body.base_url is not None:
        settings.base_url = body.base_url
    if body.timeout_s is not None:
        settings.timeout_s = body.timeout_s
    if body.max_response_chars is not None:
        settings.max_response_chars = body.max_response_chars
    if body.retry_safe_requests is not None:
        settings.retry_safe_requests = body.retry_safe_requests
    if body.max_retries is not None:
        settings.max_retries = body.max_retries
    if body.naming_style is not None:
        settings.naming_style = body.naming_style
    if body.include_writes_default is not None:
        settings.include_writes_default = body.include_writes_default
    if body.auth_mapping is not None:
        settings.auth_mapping = json.dumps(body.auth_mapping)
    if body.transports is not None:
        settings.transports = json.dumps(body.transports)
    if body.tool_prefix is not None:
        settings.tool_prefix = body.tool_prefix.strip() if body.tool_prefix else None

    await db.commit()
    await db.refresh(settings)

    auth_dict = json.loads(settings.auth_mapping) if settings.auth_mapping else {}
    transports_list = (
        json.loads(settings.transports) if settings.transports else ["stdio", "streamable-http"]
    )

    return {
        "project_id": settings.project_id,
        "base_url": settings.base_url,
        "timeout_s": settings.timeout_s,
        "max_response_chars": settings.max_response_chars,
        "retry_safe_requests": settings.retry_safe_requests,
        "max_retries": settings.max_retries,
        "naming_style": settings.naming_style,
        "include_writes_default": settings.include_writes_default,
        "auth_mapping": auth_dict,
        "transports": transports_list,
        "tool_prefix": settings.tool_prefix,
    }
