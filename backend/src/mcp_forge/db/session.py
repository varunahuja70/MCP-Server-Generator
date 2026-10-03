"""Async SQLite database session management and WAL mode configuration."""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import delete, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mcp_forge.config import Settings, get_settings
from mcp_forge.db.models.trace_event import TraceEvent

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def reset_engine() -> None:
    """Dispose and clear global engine and session factory."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    _session_factory = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Initialize or return the cached async SQLAlchemy engine."""
    global _engine
    if _engine is None:
        cfg = settings or get_settings()
        assert cfg.database_url is not None

        # Ensure database directory exists
        cfg.forge_data_dir.mkdir(parents=True, exist_ok=True)

        _engine = create_async_engine(
            cfg.database_url,
            echo=(cfg.env == "development"),
            future=True,
        )

        # Enforce WAL mode, foreign keys, and normal sync on SQLite connections
        @event.listens_for(_engine.sync_engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def get_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Return the async session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(settings)
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


@asynccontextmanager
async def get_db_session(
    settings: Settings | None = None,
) -> AsyncGenerator[AsyncSession]:
    """Async context manager yielding a database session with transaction management."""
    factory = get_session_factory(settings)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def purge_old_traces(session: AsyncSession, retention_days: int = 7) -> int:
    """Purge trace events older than retention_days. Returns count of deleted events."""
    cutoff_ts = time.time() - (retention_days * 86400)
    cutoff_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(cutoff_ts))

    stmt = delete(TraceEvent).where(TraceEvent.created_at < cutoff_iso)
    result = await session.execute(stmt)
    await session.commit()
    return int(result.rowcount)  # type: ignore[attr-defined]
