"""Resolve and normalize database URLs for Agno SQLTools (sync SQLAlchemy engine)."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote

from sqlalchemy.engine import make_url
from sqlalchemy.engine.url import URL


def normalize_sync_database_url(url: str) -> str:
    """Convert async SQLite dialect to sync URL suitable for SQLAlchemy create_engine."""
    if not url:
        return url
    # aiosqlite async URL -> sync sqlite
    out = url.replace("sqlite+aiosqlite://", "sqlite+pysqlite://", 1)
    if out == url:
        out = url.replace("sqlite+aiosqlite:", "sqlite+pysqlite:", 1)
    return out


def _sqlite_database_path(url: URL) -> Path | None:
    """Return filesystem path for a SQLite URL, or None if not SQLite."""
    try:
        dialect = url.get_dialect().name
    except Exception:
        dialect = ""
    if dialect != "sqlite":
        return None
    database = url.database
    if database is None or database == ":memory:":
        return None
    return Path(unquote(database))


def resolve_sqlite_path_to_workspace(url: str, workspace: Path) -> str:
    """If URL is SQLite with a relative database path, resolve it against workspace."""
    u = make_url(normalize_sync_database_url(url))
    db_path = _sqlite_database_path(u)
    if db_path is None:
        return normalize_sync_database_url(url)
    if db_path.is_absolute():
        return u.render_as_string(hide_password=False)
    resolved = (workspace / db_path).resolve()
    new_u = u.set(database=str(resolved))
    return new_u.render_as_string(hide_password=False)


def resolve_database_url_for_tools(
    workspace: Path,
    explicit_url: str | None = None,
    skip_db: bool = False,
) -> str | None:
    """Resolve DB URL for SQLTools: CLI override, then DATABASE_URL, then default SQLite file.

    Returns None when skip_db is True. Otherwise returns a sync SQLAlchemy URL string.
    """
    if skip_db:
        return None

    if explicit_url:
        return resolve_sqlite_path_to_workspace(explicit_url.strip(), workspace)

    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        return resolve_sqlite_path_to_workspace(env_url, workspace)

    default_file = workspace / "data" / "app.db"
    return f"sqlite+pysqlite:///{default_file.resolve()}"


def database_file_exists(url: str) -> bool:
    """Return True if SQLite URL points to an existing file (or non-SQLite URL)."""
    u = make_url(url)
    p = _sqlite_database_path(u)
    if p is None:
        return True
    return p.is_file()
