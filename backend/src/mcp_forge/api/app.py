"""FastAPI application factory for MCP Forge."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mcp_forge.api.middleware import (
    CSRFProtectionMiddleware,
    HostAllowlistMiddleware,
    SecurityHeadersMiddleware,
)
from mcp_forge.config import Settings, get_settings
from mcp_forge.errors import ForgeError
from mcp_forge.logging_setup import setup_logging
from mcp_forge.version import __version__


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app_settings = settings or get_settings()

    # Configure structured logging
    setup_logging(log_level=app_settings.log_level)

    # OpenAPI docs only in development
    docs_url = "/api/docs" if app_settings.env == "development" else None
    redoc_url = "/api/redoc" if app_settings.env == "development" else None
    openapi_url = "/api/openapi.json" if app_settings.env == "development" else None

    app = FastAPI(
        title="MCP Forge API",
        version=__version__,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    # Store settings in app state
    app.state.settings = app_settings

    # Middleware stack (executed in reverse registration order)
    # 1. Security Headers (outermost)
    app.add_middleware(SecurityHeadersMiddleware)
    # 2. Host Header validation
    app.add_middleware(HostAllowlistMiddleware, settings=app_settings)
    # 3. State-change validation (CSRF / X-Forge-Request)
    app.add_middleware(CSRFProtectionMiddleware, settings=app_settings)

    # Strict CORS: only same-origin unless explicitly required
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        allow_headers=["*"],
    )

    # Global Exception Handlers ensuring the single error shape
    @app.exception_handler(ForgeError)
    async def forge_error_handler(request: Request, exc: ForgeError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        # Strip internal repr objects for clean, safe output
        errors = [
            {
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data.",
                    "details": errors,
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail_msg = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": detail_msg,
                    "details": exc.detail if not isinstance(exc.detail, str) else {},
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Hide internal error details from response
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected internal error occurred.",
                    "details": {},
                }
            },
        )

    # Base operational endpoints
    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> JSONResponse:
        """Readiness probe checking storage and database accessibility."""
        data_dir = app_settings.forge_data_dir
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            # Verify data dir is writable by touching a temporary probe
            probe_file = data_dir / ".ready_probe"
            probe_file.write_text("ok", encoding="utf-8")
            probe_file.unlink(missing_ok=True)
            return JSONResponse(status_code=200, content={"status": "ready"})
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "NOT_READY",
                        "message": "Storage directory is not writable.",
                        "details": {"error": str(e)},
                    }
                },
            )

    @app.get("/version")
    async def version() -> dict[str, str]:
        """Version and operating mode."""
        return {
            "version": __version__,
            "mode": app_settings.forge_mode,
            "env": app_settings.env,
        }

    # Register API routers
    from mcp_forge.api.routes import (
        auth_router,
        builds_router,
        operations_router,
        playground_router,
        project_builds_router,
        projects_router,
        review_router,
        samples_router,
        settings_router,
        specs_router,
    )

    app.include_router(auth_router)
    app.include_router(samples_router)
    app.include_router(projects_router)
    app.include_router(specs_router)
    app.include_router(operations_router)
    app.include_router(settings_router)
    app.include_router(review_router)
    app.include_router(project_builds_router)
    app.include_router(builds_router)
    app.include_router(playground_router)

    return app
