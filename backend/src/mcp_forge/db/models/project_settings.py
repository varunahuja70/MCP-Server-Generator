"""ProjectSettings database model."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_forge.db.base import Base


class ProjectSettings(Base):
    """Configuration options for MCP server code generation and runtime."""

    __tablename__ = "project_settings"

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("project.id", ondelete="CASCADE"),
        primary_key=True,
    )
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    timeout_s: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_response_chars: Mapped[int] = mapped_column(Integer, default=20000, nullable=False)
    retry_safe_requests: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    naming_style: Mapped[str] = mapped_column(String(16), default="snake", nullable=False)
    include_writes_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auth_mapping: Mapped[str] = mapped_column(Text, default="{}", nullable=False)  # JSON
    transports: Mapped[str] = mapped_column(
        Text, default='["stdio","streamable-http"]', nullable=False
    )  # JSON list
    tool_prefix: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="settings")
