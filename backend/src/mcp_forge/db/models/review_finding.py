"""ReviewFinding database model."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_forge.db.base import Base
from mcp_forge.db.uuid_helper import utcnow_iso, uuidv7


class ReviewFinding(Base):
    """Linter / security finding produced during spec review."""

    __tablename__ = "review_finding"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuidv7)
    build_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("build.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # error, warning, info
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    operation_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[str] = mapped_column(String(32), default=utcnow_iso, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="findings")
    spec_version = relationship("SpecVersion", back_populates="findings")
    build = relationship("Build", back_populates="findings")
