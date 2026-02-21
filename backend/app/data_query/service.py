"""Backend tool provider for DataQueryAgent: list tasks by date range, completion stats, projects."""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db.models import Todo


def _todo_summary_dict(todo: Any) -> dict[str, Any]:
    """Convert Todo ORM object to a serializable summary for tool results."""
    return {
        "id": todo.id,
        "title": todo.title,
        "description": (todo.description or "")[:500],
        "status": todo.status,
        "urgency": todo.urgency,
        "importance": todo.importance,
        "category": todo.category,
        "tags": todo.tags or "",
        "project_id": todo.project_id,
        "created_at": todo.created_at.isoformat() if todo.created_at else None,
        "updated_at": todo.updated_at.isoformat() if todo.updated_at else None,
        "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
    }


class BackendDataQueryToolProvider:
    """
    Implements data-query tools for the DataQueryAgent using backend DB/crud.
    Pass an AsyncSession (e.g. from Depends(get_db)) so tools run in backend context.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def list_tasks_completed_since(
        self,
        since: datetime,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return tasks completed on or after the given datetime (UTC)."""
        todos, _ = await crud.get_todos(
            db=self._db,
            skip=0,
            limit=limit,
            status="Completed",
            completed_after=since,
        )
        return [_todo_summary_dict(t) for t in todos]

    async def list_tasks_updated_between(
        self,
        updated_after: datetime,
        updated_before: datetime,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return tasks that were updated between the two datetimes (UTC)."""
        todos, _ = await crud.get_todos(
            db=self._db,
            skip=0,
            limit=limit,
            updated_after=updated_after,
            updated_before=updated_before,
        )
        return [_todo_summary_dict(t) for t in todos]

    async def get_task_completion_stats(self, since: datetime) -> list[dict[str, Any]]:
        """Return counts of completed tasks by month from since to now. Each item: {\"period\": \"YYYY-MM\", \"count\": N}."""
        return await crud.get_tasks_completed_counts_by_month(db=self._db, since=since)

    async def list_projects(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return list of projects (id, name, status, organization_id)."""
        projects, _ = await crud.get_projects(db=self._db, skip=0, limit=limit)
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": (p.description or "")[:300],
                "status": p.status,
                "organization_id": p.organization_id,
            }
            for p in projects
        ]

    async def list_tasks_by_project(
        self,
        project_id: int,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return tasks for a specific project."""
        todos, _ = await crud.get_todos_by_project(
            db=self._db,
            project_id=project_id,
            skip=0,
            limit=limit,
        )
        return [_todo_summary_dict(t) for t in todos]
