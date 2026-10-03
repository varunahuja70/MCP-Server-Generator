"""Application configuration and settings for MCP Forge."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from mcp_forge.errors import UnsafeConfigError

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}


class Settings(BaseSettings):
    """MCP Forge core settings with strict security validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["development", "production"] = Field(
        default="production",
        description="Runtime environment.",
    )
    forge_mode: Literal["local", "exposed"] = Field(
        default="local",
        description="Operating mode: local (binds loopback, no auth) or exposed (requires access token).",
    )
    forge_host: str = Field(
        default="127.0.0.1",
        description="Host interface to bind.",
    )
    forge_port: int = Field(
        default=8080,
        description="Port to listen on.",
    )
    forge_public_host: str | None = Field(
        default=None,
        description="Public host name for reverse-proxy Host allowlisting.",
    )
    forge_access_token: str | None = Field(
        default=None,
        description="Secret bearer access token required in exposed mode.",
    )
    forge_data_dir: Path = Field(
        default=Path("./data"),
        description="Directory for SQLite database, build artifacts, and session scratchpads.",
    )
    database_url: str | None = Field(
        default=None,
        description="Async SQLAlchemy database connection string.",
    )
    max_spec_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum specification file size in bytes (default 10MB).",
    )
    pipeline_timeout_s: int = Field(
        default=30,
        description="Maximum wall-clock execution time for parsing/generation pipelines.",
    )
    playground_enabled: bool | None = Field(
        default=None,
        description="Whether to permit spawning playground server processes.",
    )
    playground_max_sessions: int = Field(
        default=3,
        description="Maximum concurrent active playground sessions.",
    )
    playground_idle_timeout_s: int = Field(
        default=900,
        description="Maximum idle time before auto-terminating a playground session.",
    )
    trace_retention_days: int = Field(
        default=7,
        description="Days to retain playground trace events before purge.",
    )
    allow_private_spec_urls: bool = Field(
        default=False,
        description="Allow fetching specs from private RFC1918 / loopback addresses (SSRF override).",
    )
    allow_remote_refs: bool = Field(
        default=False,
        description="Allow fetching remote JSON/YAML $ref references.",
    )
    log_level: str = Field(
        default="info",
        description="Logging level: debug, info, warning, error.",
    )

    @model_validator(mode="after")
    def validate_security_constraints(self) -> "Settings":
        # Ensure data directory path is resolved
        self.forge_data_dir = self.forge_data_dir.resolve()

        # Enforce exposed mode requirements
        if self.forge_mode == "exposed":
            if not self.forge_access_token or len(self.forge_access_token.strip()) < 16:
                raise UnsafeConfigError(
                    "FORGE_MODE=exposed requires FORGE_ACCESS_TOKEN to be set to a secure token "
                    "of at least 16 characters."
                )

        # Enforce local mode host binding restrictions
        if self.forge_mode == "local":
            host_clean = self.forge_host.strip().lower()
            if host_clean not in LOOPBACK_HOSTS:
                raise UnsafeConfigError(
                    f"Binding to non-loopback host '{self.forge_host}' is prohibited in local mode. "
                    "Use FORGE_MODE=exposed and set FORGE_ACCESS_TOKEN to run on an exposed interface."
                )

        # Default playground_enabled based on mode if not explicitly provided
        if self.playground_enabled is None:
            self.playground_enabled = self.forge_mode == "local"

        # Derive database URL if not explicitly provided
        if not self.database_url:
            db_path = (self.forge_data_dir / "forge.sqlite3").as_posix()
            self.database_url = f"sqlite+aiosqlite:///{db_path}"

        return self


def get_settings() -> Settings:
    """Load settings instance."""
    return Settings()
