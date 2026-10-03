"""OperationConfig database model."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_forge.db.base import Base


class OperationConfig(Base):
    """User selections, overrides, and customization for an operation."""

    __tablename__ = "operation_config"

    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("project.id", ondelete="CASCADE"),
        primary_key=True,
    )
    operation_key: Mapped[str] = mapped_column(
        String(256),
        primary_key=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tool_name_override: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description_override: Mapped[str | None] = mapped_column(Text, nullable=True)
    group_override: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="operations")
