"""Authentication endpoints for exposed mode: login with token and session cookie."""

import hmac

from fastapi import APIRouter, Depends, Response

from mcp_forge.api.deps import get_current_settings
from mcp_forge.api.schemas.models import LoginRequest, LoginResponse
from mcp_forge.config import Settings
from mcp_forge.errors import UnauthorizedError

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    settings: Settings = Depends(get_current_settings),
) -> dict[str, str]:
    """Authenticate in exposed mode and obtain an HTTP-only session cookie."""
    if settings.forge_mode == "local":
        return {"status": "ok", "message": "Authentication not required in local mode"}

    if not settings.forge_access_token:
        raise UnauthorizedError("No access token configured on server.")

    # Constant time compare
    if not hmac.compare_digest(
        body.token.encode("utf-8"), settings.forge_access_token.encode("utf-8")
    ):
        raise UnauthorizedError("Invalid access token.")

    # Set httpOnly cookie
    response.set_cookie(
        key="forge_session",
        value=body.token,
        httponly=True,
        samesite="lax",
        secure=(settings.env == "production"),
        path="/",
    )

    return {"status": "ok", "message": "Logged in successfully"}


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """Clear session cookie."""
    response.delete_cookie(key="forge_session", path="/")
    return {"status": "ok", "message": "Logged out"}
