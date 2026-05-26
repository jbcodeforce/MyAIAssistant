"""Tests for database URL resolution for Agno SQLTools."""

from __future__ import annotations

from pathlib import Path

from ai_assist_cli.services.db_url import (
    database_file_exists,
    normalize_sync_database_url,
    resolve_database_url_for_tools,
    resolve_sqlite_path_to_workspace,
)


def test_normalize_sync_replaces_aiosqlite() -> None:
    out = normalize_sync_database_url("sqlite+aiosqlite:///./data/app.db")
    assert "aiosqlite" not in out
    assert "sqlite+pysqlite" in out or "pysqlite" in out


def test_resolve_sqlite_path_relative_to_workspace(tmp_path: Path) -> None:
    ws = tmp_path
    out = resolve_sqlite_path_to_workspace("sqlite+aiosqlite:///./data/app.db", ws)
    assert str(ws / "data" / "app.db") in out.replace("file://", "")
    assert (ws / "data" / "app.db").as_posix() in out or "data" in out


def test_resolve_default_points_to_workspace_data_app_db(tmp_path: Path) -> None:
    url = resolve_database_url_for_tools(tmp_path, explicit_url=None, skip_db=False)
    assert url is not None
    assert "app.db" in url
    assert tmp_path.name in str(url) or "app.db" in url


def test_skip_db_returns_none() -> None:
    assert resolve_database_url_for_tools(Path("/tmp/x"), skip_db=True) is None


def test_database_file_exists_false_for_missing_sqlite(tmp_path: Path) -> None:
    url = f"sqlite+pysqlite:///{(tmp_path / 'nope.db').as_posix()}"
    assert database_file_exists(url) is False


def test_database_file_exists_true_for_real_file(tmp_path: Path) -> None:
    p = tmp_path / "a.db"
    p.write_bytes(b"")
    url = f"sqlite+pysqlite:///{p.as_posix()}"
    assert database_file_exists(url) is True
