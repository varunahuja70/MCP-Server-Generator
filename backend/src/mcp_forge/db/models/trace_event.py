"""TraceEvent database model."""

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcp_forge.db.base import Base
from mcp_forge.db.uuid_helper import utcnow_iso, uuidv7


class TraceEvent(Base):
    """Protocol trace message exchanged with a running MCP server in playground."""

    __tablename__ = "trace_event"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuidv7)
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("playground_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(
        String(24), nullable=False
    )  # client_to_server, server_to_client, stderr
    message_json: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), default=utcnow_iso, nullable=False)

    # Relationships
    session = relationship("PlaygroundSession", back_populates="traces")
