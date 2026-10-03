"""AppSetting database model."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from mcp_forge.db.base import Base


class AppSetting(Base):
    """Global key-value configuration state and hashes stored in database."""

    __tablename__ = "app_setting"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON formatted
