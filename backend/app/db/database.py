from pathlib import Path
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.db.models import Base


# Singleton instances - initialized lazily
_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker] = None


def is_sqlite_url(database_url: str) -> bool:
    """Check if the database URL is for SQLite."""
    return database_url.startswith("sqlite")


def get_engine() -> AsyncEngine:
    """Get or create the database engine singleton.
    
    Automatically detects SQLite vs PostgreSQL from the database URL
    and applies appropriate engine configuration.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url
        
        if is_sqlite_url(database_url):
            # SQLite-specific configuration
            # Extract path and ensure directory exists
            # URL format: sqlite+aiosqlite:///./path/to/db.sqlite or sqlite+aiosqlite:////absolute/path
            if ":///" in database_url:
                path_part = database_url.split(":///", 1)[1]
                if path_part and path_part != ":memory:":
                    db_path = Path(path_part)
                    if not db_path.is_absolute():
                        # Resolve relative to current working directory
                        db_path = Path.cwd() / path_part
                    db_path.parent.mkdir(parents=True, exist_ok=True)
            
            _engine = create_async_engine(
                database_url,
                echo=True,
                future=True,
                connect_args={"check_same_thread": False},
            )
        else:
            # PostgreSQL configuration
            _engine = create_async_engine(
                database_url,
                echo=True,
                future=True,
            )
    return _engine


def get_session_maker() -> async_sessionmaker:
    """Get or create the session maker singleton."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get a database session."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def reset_engine() -> None:
    """Reset the engine singleton. Useful for testing."""
    global _engine, _async_session_maker
    _engine = None
    _async_session_maker = None
