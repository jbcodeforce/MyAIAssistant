from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Todo, Knowledge
from app.api.schemas.todo import TodoCreate, TodoUpdate


async def create_todo(db: AsyncSession, todo: TodoCreate) -> Todo:
    db_todo = Todo(**todo.model_dump())
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)
    return db_todo


async def get_todo(db: AsyncSession, todo_id: int) -> Optional[Todo]:
    result = await db.execute(select(Todo).where(Todo.id == todo_id))
    return result.scalar_one_or_none()


def _search_condition(term: str):
    """Case-insensitive title/description match (SQLite + PostgreSQL)."""
    pattern = f"%{term}%"
    return or_(
        func.lower(Todo.title).like(pattern),
        (
            Todo.description.isnot(None)
            & func.lower(Todo.description).like(pattern)
        ),
    )


async def get_todos(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    importance: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> tuple[list[Todo], int]:
    conditions = []

    if search and search.strip():
        term = search.strip().lower()[:200]
        conditions.append(_search_condition(term))
    if status:
        status_list = [s.strip() for s in status.split(',')]
        if len(status_list) == 1:
            conditions.append(Todo.status == status_list[0])
        else:
            conditions.append(Todo.status.in_(status_list))
    if urgency:
        conditions.append(Todo.urgency == urgency)
    if importance:
        conditions.append(Todo.importance == importance)
    if category:
        conditions.append(Todo.category == category)

    base_filter = and_(*conditions) if conditions else True
    query = select(Todo).where(base_filter)

    # Count with same filter (flat query so bind params apply correctly)
    count_query = select(func.count()).select_from(Todo).where(base_filter)
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Todo.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    todos = list(result.scalars().all())

    return todos, total


async def update_todo(
    db: AsyncSession, 
    todo_id: int, 
    todo_update: TodoUpdate
) -> Optional[Todo]:
    db_todo = await get_todo(db, todo_id)
    if not db_todo:
        return None
    
    update_data = todo_update.model_dump(exclude_unset=True)
    
    # If status is being changed to Completed, set completed_at
    if "status" in update_data and update_data["status"] == "Completed":
        update_data["completed_at"] = datetime.now(timezone.utc)
    
    for field, value in update_data.items():
        setattr(db_todo, field, value)
    
    await db.commit()
    await db.refresh(db_todo)
    return db_todo


async def delete_todo(db: AsyncSession, todo_id: int) -> bool:
    db_todo = await get_todo(db, todo_id)
    if not db_todo:
        return False
    
    await db.delete(db_todo)
    await db.commit()
    return True


async def get_todos_by_urgency_importance(
    db: AsyncSession,
    urgency: str,
    importance: str,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Todo], int]:
    return await get_todos(
        db=db,
        skip=skip,
        limit=limit,
        urgency=urgency,
        importance=importance,
        status="Open"  # Only get open todos for the canvas view
    )


async def get_unclassified_todos(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Todo], int]:
    query = select(Todo).where(
        (Todo.urgency.is_(None)) | (Todo.importance.is_(None))
    )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Todo.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    todos = list(result.scalars().all())
    
    return todos, total


async def get_todos_by_project(
    db: AsyncSession,
    project_id: int,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Todo], int]:
    """Get all todos for a specific project."""
    query = select(Todo).where(Todo.project_id == project_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Todo.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    todos = list(result.scalars().all())
    
    return todos, total


async def count_active_todos_for_project(db: AsyncSession, project_id: int) -> int:
    """Count active todos (Open or Started) for a project."""
    query = select(func.count()).where(
        Todo.project_id == project_id,
        Todo.status.in_(["Open", "Started"])
    )
    result = await db.execute(query)
    return result.scalar_one()


def _parse_tags_from_strings(tag_strings: list[str]) -> list[str]:
    """Parse comma-separated tag strings into a sorted list of unique tags."""
    seen: set[str] = set()
    for s in tag_strings:
        if not s or not s.strip():
            continue
        for part in s.split(","):
            tag = part.strip()
            if tag:
                seen.add(tag)
    return sorted(seen)


async def get_distinct_tags(
    db: AsyncSession,
    include_knowledge: bool = True,
) -> list[str]:
    """
    Return distinct tag values from Todo.tags and optionally Knowledge.tags.
    Tags are stored as comma-separated strings; they are split, trimmed, and deduplicated.
    """
    tag_strings: list[str] = []
    result = await db.execute(select(Todo.tags).where(Todo.tags.isnot(None)))
    for val in result.scalars():
        if val and isinstance(val, str):
            tag_strings.append(val.strip())
    if include_knowledge:
        result = await db.execute(select(Knowledge.tags).where(Knowledge.tags.isnot(None)))
        for val in result.scalars():
            if val and isinstance(val, str):
                tag_strings.append(val.strip())
    return _parse_tags_from_strings(tag_strings)

