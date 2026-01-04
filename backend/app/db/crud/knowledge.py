from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Knowledge
from app.api.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate


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

