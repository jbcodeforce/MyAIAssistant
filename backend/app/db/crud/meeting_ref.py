from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MeetingRef


async def create_meeting_ref(
    db: AsyncSession,
    meeting_id: str,
    file_ref: str,
    project_id: Optional[int] = None,
    org_id: Optional[int] = None,
) -> MeetingRef:
    """Create a new meeting reference."""
    db_meeting_ref = MeetingRef(
        meeting_id=meeting_id,
        file_ref=file_ref,
        project_id=project_id,
        org_id=org_id,
    )
    db.add(db_meeting_ref)
    await db.commit()
    await db.refresh(db_meeting_ref)
    return db_meeting_ref


async def get_meeting_ref(db: AsyncSession, meeting_ref_id: int) -> Optional[MeetingRef]:
    """Get a meeting reference by ID."""
    result = await db.execute(select(MeetingRef).where(MeetingRef.id == meeting_ref_id))
    return result.scalar_one_or_none()


async def get_meeting_ref_by_meeting_id(db: AsyncSession, meeting_id: str) -> Optional[MeetingRef]:
    """Get a meeting reference by meeting_id."""
    result = await db.execute(select(MeetingRef).where(MeetingRef.meeting_id == meeting_id))
    return result.scalar_one_or_none()


async def get_meeting_refs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    org_id: Optional[int] = None,
) -> tuple[list[MeetingRef], int]:
    """Get all meeting references with pagination and optional filters."""
    query = select(MeetingRef)
    
    # Apply filters
    if project_id is not None:
        query = query.where(MeetingRef.project_id == project_id)
    if org_id is not None:
        query = query.where(MeetingRef.org_id == org_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(MeetingRef.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    meeting_refs = list(result.scalars().all())
    
    return meeting_refs, total


async def update_meeting_ref(
    db: AsyncSession,
    meeting_ref_id: int,
    project_id: Optional[int] = None,
    org_id: Optional[int] = None,
    update_project_id: bool = False,
    update_org_id: bool = False,
) -> Optional[MeetingRef]:
    """Update an existing meeting reference.
    
    Args:
        db: Database session
        meeting_ref_id: ID of the meeting reference to update
        project_id: New project ID (only applied if update_project_id is True)
        org_id: New organization ID (only applied if update_org_id is True)
        update_project_id: Whether to update project_id (allows setting to None)
        update_org_id: Whether to update org_id (allows setting to None)
    """
    db_meeting_ref = await get_meeting_ref(db, meeting_ref_id)
    if not db_meeting_ref:
        return None
    
    if update_project_id:
        db_meeting_ref.project_id = project_id
    if update_org_id:
        db_meeting_ref.org_id = org_id
    
    await db.commit()
    await db.refresh(db_meeting_ref)
    return db_meeting_ref


async def delete_meeting_ref(db: AsyncSession, meeting_ref_id: int) -> bool:
    """Delete a meeting reference by ID."""
    db_meeting_ref = await get_meeting_ref(db, meeting_ref_id)
    if not db_meeting_ref:
        return False
    
    await db.delete(db_meeting_ref)
    await db.commit()
    return True


async def get_meeting_refs_by_project(
    db: AsyncSession,
    project_id: int,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[MeetingRef], int]:
    """Get all meeting references for a specific project."""
    return await get_meeting_refs(db, skip=skip, limit=limit, project_id=project_id)


async def get_meeting_refs_by_organization(
    db: AsyncSession,
    org_id: int,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[MeetingRef], int]:
    """Get all meeting references for a specific organization."""
    return await get_meeting_refs(db, skip=skip, limit=limit, org_id=org_id)
