"""API route modules package."""

from mcp_forge.api.routes.auth import router as auth_router
from mcp_forge.api.routes.builds import builds_router, project_builds_router
from mcp_forge.api.routes.operations import router as operations_router
from mcp_forge.api.routes.playground import router as playground_router
from mcp_forge.api.routes.projects import router as projects_router
from mcp_forge.api.routes.review import router as review_router
from mcp_forge.api.routes.samples import router as samples_router
from mcp_forge.api.routes.settings import router as settings_router
from mcp_forge.api.routes.specs import router as specs_router

__all__ = [
    "auth_router",
    "builds_router",
    "operations_router",
    "playground_router",
    "project_builds_router",
    "projects_router",
    "review_router",
    "samples_router",
    "settings_router",
    "specs_router",
]
