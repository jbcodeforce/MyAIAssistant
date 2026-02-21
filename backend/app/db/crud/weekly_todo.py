import logging
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WeeklyTodo, WeeklyTodoAllocation
from app.api.schemas.weekly_todo import WeeklyTodoCreate, WeeklyTodoUpdate, AllocationDayMinutes
from app.api.schemas.todo import TodoCreate
from app.db.crud.todo import create_todo

logger = logging.getLogger(__name__)


async def create_weekly_todo(db: AsyncSession, data: WeeklyTodoCreate) -> WeeklyTodo:
    """Create a new weekly todo. If todo_id is not provided, create an unclassified todo and link it."""
    logger.debug("create_weekly_todo title=%r todo_id=%s", data.title, data.todo_id)
    todo_id = data.todo_id
    if todo_id is None or todo_id == 0:
        new_todo = await create_todo(
            db,
            TodoCreate(
                title=data.title,
                description=data.description,
                status="Open",
                urgency=None,
                importance=None,
            ),
        )
        todo_id = new_todo.id
    payload = data.model_dump()
    payload["todo_id"] = todo_id
    db_item = WeeklyTodo(**payload)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    logger.debug("create_weekly_todo created id=%s todo_id=%s", db_item.id, db_item.todo_id)
    return db_item


async def get_weekly_todo(db: AsyncSession, weekly_todo_id: int) -> Optional[WeeklyTodo]:
    """Get a weekly todo by ID."""
    logger.debug("get_weekly_todo weekly_todo_id=%s", weekly_todo_id)
    result = await db.execute(
        select(WeeklyTodo).where(WeeklyTodo.id == weekly_todo_id)
    )
    return result.scalar_one_or_none()


async def get_weekly_todos(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[WeeklyTodo], int]:
    """List weekly todos with pagination."""
    logger.debug("get_weekly_todos skip=%s limit=%s", skip, limit)
    query = select(WeeklyTodo)
    count_result = await db.execute(select(func.count()).select_from(WeeklyTodo))
    total = count_result.scalar_one()
    query = query.order_by(WeeklyTodo.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())
    return items, total


async def update_weekly_todo(
    db: AsyncSession,
    weekly_todo_id: int,
    data: WeeklyTodoUpdate,
) -> Optional[WeeklyTodo]:
    """Update a weekly todo."""
    logger.debug("update_weekly_todo weekly_todo_id=%s", weekly_todo_id)
    item = await get_weekly_todo(db, weekly_todo_id)
    if not item:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_weekly_todo(db: AsyncSession, weekly_todo_id: int) -> bool:
    """Delete a weekly todo (allocations are cascade-deleted)."""
    logger.debug("delete_weekly_todo weekly_todo_id=%s", weekly_todo_id)
    item = await get_weekly_todo(db, weekly_todo_id)
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def get_allocation(
    db: AsyncSession,
    weekly_todo_id: int,
    week_key: str,
) -> Optional[WeeklyTodoAllocation]:
    """Get allocation for a weekly todo and week."""
    result = await db.execute(
        select(WeeklyTodoAllocation).where(
            WeeklyTodoAllocation.weekly_todo_id == weekly_todo_id,
            WeeklyTodoAllocation.week_key == week_key,
        )
    )
    return result.scalar_one_or_none()


async def set_allocation(
    db: AsyncSession,
    weekly_todo_id: int,
    week_key: str,
    data: AllocationDayMinutes,
) -> WeeklyTodoAllocation:
    """Create or update allocation for a weekly todo and week."""
    logger.debug(
        "set_allocation weekly_todo_id=%s week_key=%s mon=%s tue=%s ...",
        weekly_todo_id, week_key, data.mon, data.tue,
    )
    existing = await get_allocation(db, weekly_todo_id, week_key)
    payload = data.model_dump()
    if existing:
        existing.mon = payload["mon"]
        existing.tue = payload["tue"]
        existing.wed = payload["wed"]
        existing.thu = payload["thu"]
        existing.fri = payload["fri"]
        existing.sat = payload["sat"]
        existing.sun = payload["sun"]
        await db.commit()
        await db.refresh(existing)
        return existing
    allocation = WeeklyTodoAllocation(
        weekly_todo_id=weekly_todo_id,
        week_key=week_key,
        **payload,
    )
    db.add(allocation)
    await db.commit()
    await db.refresh(allocation)
    return allocation


async def list_allocations_for_week(
    db: AsyncSession,
    week_key: str,
) -> list[WeeklyTodoAllocation]:
    """List all allocations for a given week_key."""
    logger.debug("list_allocations_for_week week_key=%s", week_key)
    result = await db.execute(
        select(WeeklyTodoAllocation)
        .where(WeeklyTodoAllocation.week_key == week_key)
        .order_by(WeeklyTodoAllocation.weekly_todo_id)
    )
    return list(result.scalars().all())
