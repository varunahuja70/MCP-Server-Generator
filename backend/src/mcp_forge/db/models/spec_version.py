"""SpecVersion database model."""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_forge.db.base import Base
from mcp_forge.db.uuid_helper import utcnow_iso, uuidv7


class SpecVersion(Base):
    """Immutable snapshot of an ingested OpenAPI/Swagger specification."""

    __tablename__ = "spec_version"
    __table_args__ = (UniqueConstraint("project_id", "version_no", name="uq_project_spec_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuidv7)
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)  # file, paste, url, sample
    source_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    format: Mapped[str] = mapped_column(String(8), nullable=False)  # json, yaml
    spec_kind: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # swagger2, oas30, oas31, oas32
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    operation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[str] = mapped_column(String(32), default=utcnow_iso, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="specs")
    builds = relationship("Build", back_populates="spec_version")
    findings = relationship("ReviewFinding", back_populates="spec_version")
