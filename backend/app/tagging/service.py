"""Backend tool provider for TaskTaggingAgent: get_available_tags, task_list, update_task."""

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.api.schemas.todo import TodoUpdate


def _todo_to_dict(todo: Any) -> dict[str, Any]:
    """Convert Todo ORM object to a serializable dict for tool results."""
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description or "",
        "tags": todo.tags or "",
        "status": todo.status,
        "urgency": todo.urgency,
        "importance": todo.importance,
        "category": todo.category,
    }


class BackendTaskTaggingToolProvider:
    """
    Implements TaskTaggingToolProvider using backend DB/crud.
    Pass an AsyncSession (e.g. from Depends(get_db)) so tools run in backend context.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_available_tags(self) -> list[str]:
        """Return list of existing tag strings from Todo and Knowledge."""
        return await crud.get_distinct_tags(db=self._db, include_knowledge=True)

    async def task_list(
        self,
        skip: int = 0,
        limit: int = 100,
        todo_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Return list of tasks; if todo_id is set, return that task only."""
        if todo_id is not None:
            todo = await crud.get_todo(db=self._db, todo_id=todo_id)
            if not todo:
                return []
            return [_todo_to_dict(todo)]
        todos, _ = await crud.get_todos(db=self._db, skip=skip, limit=limit)
        return [_todo_to_dict(t) for t in todos]

    async def update_task(self, todo_id: int, tags: list[str]) -> dict[str, Any]:
        """Update the given task's tags. Returns updated task info or error."""
        tags_str = ",".join(str(t).strip() for t in tags if str(t).strip())
        todo_update = TodoUpdate(tags=tags_str or None)
        updated = await crud.update_todo(db=self._db, todo_id=todo_id, todo_update=todo_update)
        if not updated:
            return {"success": False, "error": "Todo not found"}
        return {"success": True, "id": updated.id, "tags": updated.tags or ""}
