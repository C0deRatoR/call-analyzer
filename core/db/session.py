"""SQLAlchemy engines + session factories.

Two engines coexist because the API and the worker have different concurrency
models:

- **`engine` (async / asyncpg)** — used by FastAPI request handlers via
  the `get_db` dependency.

- **`sync_engine` (sync / psycopg2)** — used by Celery tasks. Async engines
  bind their connection pool to a single event loop; reusing one across
  `asyncio.run()` invocations (one per Celery task) silently corrupts the
  pool. Sync is the conventional Celery pattern.

Alembic uses the async engine via its own env.py.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings

# ---- Async (FastAPI) ----------------------------------------------------

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields one session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---- Sync (Celery worker) -----------------------------------------------


def _sync_database_url() -> str:
    """Translate an `asyncpg` URL to its `psycopg2` equivalent.

    Settings.database_url is async-shaped (`postgresql+asyncpg://...`) so the
    same env var works for both engines without extra config.
    """
    return settings.database_url.replace("+asyncpg", "+psycopg2")


sync_engine = create_engine(
    _sync_database_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)


def get_sync_db() -> Session:
    """Open a sync session. Caller is responsible for closing it (or use a
    `with SyncSessionLocal() as session:` block)."""
    return SyncSessionLocal()
