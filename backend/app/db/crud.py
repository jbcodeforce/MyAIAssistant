from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Todo, Knowledge
from app.schemas.todo import TodoCreate, TodoUpdate
from app.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate


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


# Knowledge CRUD operations

async def create_knowledge(db: AsyncSession, knowledge: KnowledgeCreate) -> Knowledge:
    db_knowledge = Knowledge(**knowledge.model_dump())
    db.add(db_knowledge)
    await db.commit()
    await db.refresh(db_knowledge)
    return db_knowledge


async def get_knowledge(db: AsyncSession, knowledge_id: int) -> Optional[Knowledge]:
    result = await db.execute(select(Knowledge).where(Knowledge.id == knowledge_id))
    return result.scalar_one_or_none()


async def get_knowledges(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
) -> tuple[list[Knowledge], int]:
    query = select(Knowledge)
    
    if document_type:
        query = query.where(Knowledge.document_type == document_type)
    if status:
        # Support comma-separated status values
        status_list = [s.strip() for s in status.split(',')]
        if len(status_list) == 1:
            query = query.where(Knowledge.status == status_list[0])
        else:
            query = query.where(Knowledge.status.in_(status_list))
    if category:
        query = query.where(Knowledge.category == category)
    if tag:
        # Search for tag within the comma-separated tags field
        # This handles cases like: exact match, at start, at end, or in middle
        tag_lower = tag.strip().lower()
        query = query.where(
            (Knowledge.tags == tag_lower) |  # exact single tag
            (Knowledge.tags.like(f"{tag_lower},%")) |  # tag at start
            (Knowledge.tags.like(f"%,{tag_lower}")) |  # tag at end
            (Knowledge.tags.like(f"%,{tag_lower},%"))  # tag in middle
        )
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Knowledge.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())
    
    return items, total


async def update_knowledge(
    db: AsyncSession,
    knowledge_id: int,
    knowledge_update: KnowledgeUpdate
) -> Optional[Knowledge]:
    db_knowledge = await get_knowledge(db, knowledge_id)
    if not db_knowledge:
        return None
    
    update_data = knowledge_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_knowledge, field, value)
    
    await db.commit()
    await db.refresh(db_knowledge)
    return db_knowledge


async def delete_knowledge(db: AsyncSession, knowledge_id: int) -> bool:
    db_knowledge = await get_knowledge(db, knowledge_id)
    if not db_knowledge:
        return False
    
    await db.delete(db_knowledge)
    await db.commit()
    return True


async def get_knowledge_by_uri(db: AsyncSession, uri: str) -> Optional[Knowledge]:
    """Find a knowledge item by its URI."""
    result = await db.execute(select(Knowledge).where(Knowledge.uri == uri))
    return result.scalar_one_or_none()

