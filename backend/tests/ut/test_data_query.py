"""Tests for data query tool provider (BackendDataQueryToolProvider)."""

from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_query.service import BackendDataQueryToolProvider
from app.db import crud
from app.api.schemas.todo import TodoCreate, TodoUpdate


@pytest.mark.asyncio
async def test_list_tasks_completed_since(db_session: AsyncSession):
    """Provider list_tasks_completed_since returns completed tasks after since."""
    todo = await crud.create_todo(
        db_session,
        TodoCreate(title="Done task", status="Open"),
    )
    await crud.update_todo(db_session, todo.id, TodoUpdate(status="Completed"))
    provider = BackendDataQueryToolProvider(db=db_session)
    since = datetime.now(timezone.utc) - timedelta(days=1)
    tasks = await provider.list_tasks_completed_since(since=since, limit=10)
    assert isinstance(tasks, list)
    for t in tasks:
        assert "id" in t and "title" in t and "status" in t
        assert t["status"] == "Completed"


@pytest.mark.asyncio
async def test_get_task_completion_stats(db_session: AsyncSession):
    """Provider get_task_completion_stats returns list of {period, count}."""
    provider = BackendDataQueryToolProvider(db=db_session)
    since = datetime.now(timezone.utc) - timedelta(days=180)
    stats = await provider.get_task_completion_stats(since=since)
    assert isinstance(stats, list)
    for item in stats:
        assert "period" in item
        assert "count" in item
        assert isinstance(item["period"], str)
        assert isinstance(item["count"], int)


@pytest.mark.asyncio
async def test_list_projects(db_session: AsyncSession):
    """Provider list_projects returns list of project dicts."""
    provider = BackendDataQueryToolProvider(db=db_session)
    projects = await provider.list_projects(limit=10)
    assert isinstance(projects, list)
    for p in projects:
        assert "id" in p and "name" in p and "status" in p
