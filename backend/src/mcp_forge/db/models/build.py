"""Build database model."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_forge.db.base import Base
from mcp_forge.db.uuid_helper import utcnow_iso, uuidv7


class Build(Base):
    """Numbered build record representing a generated MCP server artifact."""

    __tablename__ = "build"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuidv7)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    spec_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("spec_version.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    build_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default="queued", nullable=False
    )  # queued, running, succeeded, failed
    tool_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generator_version: Mapped[str] = mapped_column(String(32), nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)
    artifact_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    error_message_safe: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), default=utcnow_iso, nullable=False)
    finished_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="builds")
    spec_version = relationship("SpecVersion", back_populates="builds")
    findings = relationship("ReviewFinding", back_populates="build")
    sessions = relationship(
        "PlaygroundSession", back_populates="build", cascade="all, delete-orphan"
    )
