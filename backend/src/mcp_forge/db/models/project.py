"""Project database model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_forge.db.base import Base
from mcp_forge.db.uuid_helper import utcnow_iso, uuidv7


class Project(Base):
    """Project entity representing an API-to-MCP workspace."""

    __tablename__ = "project"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuidv7)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(String(32), default=utcnow_iso, nullable=False)
    updated_at: Mapped[str] = mapped_column(
        String(32), default=utcnow_iso, onupdate=utcnow_iso, nullable=False
    )
    archived_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Relationships
    specs = relationship(
        "SpecVersion",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="SpecVersion.version_no.desc()",
    )
    settings = relationship(
        "ProjectSettings",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    operations = relationship(
        "OperationConfig",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    findings = relationship(
        "ReviewFinding",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    builds = relationship(
        "Build",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Build.build_no.desc()",
    )
