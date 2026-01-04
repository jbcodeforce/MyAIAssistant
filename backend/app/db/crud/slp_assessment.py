from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SLPassessment
from app.api.schemas.slp_assessment import SLPassessmentCreate, SLPassessmentEntity


async def create_slp_assessment(
    db: AsyncSession, assessment: SLPassessmentCreate
) -> SLPassessment:
    """Create a new SLP assessment."""
    # Convert Dimension objects to dicts for JSON storage
    db_assessment = SLPassessment(
        partner=assessment.partner.model_dump(),
        family=assessment.family.model_dump(),
        friends=assessment.friends.model_dump(),
        physical_health=assessment.physical_health.model_dump(),
        mental_health=assessment.mental_health.model_dump(),
        spirituality=assessment.spirituality.model_dump(),
        community=assessment.community.model_dump(),
        societal=assessment.societal.model_dump(),
        job_task=assessment.job_task.model_dump(),
        learning=assessment.learning.model_dump(),
        finance=assessment.finance.model_dump(),
        hobbies=assessment.hobbies.model_dump(),
        online_entertainment=assessment.online_entertainment.model_dump(),
        offline_entertainment=assessment.offline_entertainment.model_dump(),
        physiological_needs=assessment.physiological_needs.model_dump(),
        daily_activities=assessment.daily_activities.model_dump(),
    )
    db.add(db_assessment)
    await db.commit()
    await db.refresh(db_assessment)
    return db_assessment


async def get_slp_assessment(
    db: AsyncSession, assessment_id: int
) -> Optional[SLPassessment]:
    """Get an SLP assessment by ID."""
    result = await db.execute(
        select(SLPassessment).where(SLPassessment.id == assessment_id)
    )
    return result.scalar_one_or_none()


async def get_slp_assessments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[SLPassessment], int]:
    """Get all SLP assessments with pagination."""
    query = select(SLPassessment)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results (most recent first)
    query = query.order_by(SLPassessment.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    assessments = list(result.scalars().all())
    
    return assessments, total


async def update_slp_assessment(
    db: AsyncSession,
    assessment_id: int,
    assessment_update: SLPassessmentEntity
) -> Optional[SLPassessment]:
    """Update an existing SLP assessment."""
    db_assessment = await get_slp_assessment(db, assessment_id)
    if not db_assessment:
        return None
    
    update_data = assessment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            # Convert Dimension to dict if it's a Pydantic model
            if hasattr(value, 'model_dump'):
                value = value.model_dump()
            setattr(db_assessment, field, value)
    
    await db.commit()
    await db.refresh(db_assessment)
    return db_assessment


async def delete_slp_assessment(db: AsyncSession, assessment_id: int) -> bool:
    """Delete an SLP assessment by ID."""
    db_assessment = await get_slp_assessment(db, assessment_id)
    if not db_assessment:
        return False
    
    await db.delete(db_assessment)
    await db.commit()
    return True

