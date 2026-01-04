from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TaskPlan
from app.api.schemas.task_plan import TaskPlanCreate, TaskPlanUpdate


async def create_task_plan(db: AsyncSession, task_plan: TaskPlanCreate) -> TaskPlan:
    """Create a new task plan for a todo."""
    db_task_plan = TaskPlan(**task_plan.model_dump())
    db.add(db_task_plan)
    await db.commit()
    await db.refresh(db_task_plan)
    return db_task_plan


async def get_task_plan(db: AsyncSession, task_plan_id: int) -> Optional[TaskPlan]:
    """Get a task plan by its ID."""
    result = await db.execute(select(TaskPlan).where(TaskPlan.id == task_plan_id))
    return result.scalar_one_or_none()


async def get_task_plan_by_todo_id(db: AsyncSession, todo_id: int) -> Optional[TaskPlan]:
    """Get a task plan by the associated todo ID."""
    result = await db.execute(select(TaskPlan).where(TaskPlan.todo_id == todo_id))
    return result.scalar_one_or_none()


async def update_task_plan(
    db: AsyncSession,
    todo_id: int,
    task_plan_update: TaskPlanUpdate
) -> Optional[TaskPlan]:
    """Update an existing task plan."""
    db_task_plan = await get_task_plan_by_todo_id(db, todo_id)
    if not db_task_plan:
        return None
    
    update_data = task_plan_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task_plan, field, value)
    
    await db.commit()
    await db.refresh(db_task_plan)
    return db_task_plan


async def upsert_task_plan(
    db: AsyncSession,
    todo_id: int,
    content: str
) -> TaskPlan:
    """Create or update a task plan for a todo."""
    existing = await get_task_plan_by_todo_id(db, todo_id)
    if existing:
        existing.content = content
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        task_plan = TaskPlanCreate(todo_id=todo_id, content=content)
        return await create_task_plan(db, task_plan)


async def delete_task_plan(db: AsyncSession, todo_id: int) -> bool:
    """Delete a task plan by todo ID."""
    db_task_plan = await get_task_plan_by_todo_id(db, todo_id)
    if not db_task_plan:
        return False
    
    await db.delete(db_task_plan)
    await db.commit()
    return True

