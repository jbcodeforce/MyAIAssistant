from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Todo
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


async def get_todos(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    importance: Optional[str] = None,
    category: Optional[str] = None,
) -> tuple[list[Todo], int]:
    query = select(Todo)
    
    if status:
        # Support comma-separated status values (e.g., "Open,Started")
        status_list = [s.strip() for s in status.split(',')]
        if len(status_list) == 1:
            query = query.where(Todo.status == status_list[0])
        else:
            query = query.where(Todo.status.in_(status_list))
    if urgency:
        query = query.where(Todo.urgency == urgency)
    if importance:
        query = query.where(Todo.importance == importance)
    if category:
        query = query.where(Todo.category == category)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
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

