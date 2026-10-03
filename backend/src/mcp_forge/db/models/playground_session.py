"""PlaygroundSession database model."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_forge.db.base import Base
from mcp_forge.db.uuid_helper import utcnow_iso, uuidv7


class PlaygroundSession(Base):
    """Execution session running a generated server against mock or live targets."""

    __tablename__ = "playground_session"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuidv7)
    build_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("build.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target: Mapped[str] = mapped_column(String(16), nullable=False)  # mock, live
    status: Mapped[str] = mapped_column(
        String(16), default="starting", nullable=False
    )  # starting, running, stopped, failed
    started_at: Mapped[str] = mapped_column(String(32), default=utcnow_iso, nullable=False)
    ended_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    exit_info: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Relationships
    build = relationship("Build", back_populates="sessions")
    traces = relationship(
        "TraceEvent",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TraceEvent.seq.asc()",
    )
