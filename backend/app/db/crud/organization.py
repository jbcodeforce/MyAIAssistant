from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Organization
from app.api.schemas.organization import OrganizationCreate, OrganizationUpdate


async def create_organization(db: AsyncSession, organization: OrganizationCreate) -> Organization:
    """Create a new organization."""
    db_organization = Organization(**organization.model_dump())
    db.add(db_organization)
    await db.commit()
    await db.refresh(db_organization)
    return db_organization


async def get_organization(db: AsyncSession, organization_id: int) -> Optional[Organization]:
    """Get an organization by ID."""
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    return result.scalar_one_or_none()


async def get_organizations(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Organization], int]:
    """Get all organizations with pagination."""
    query = select(Organization)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Organization.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    organizations = list(result.scalars().all())
    
    return organizations, total


async def update_organization(
    db: AsyncSession,
    organization_id: int,
    organization_update: OrganizationUpdate
) -> Optional[Organization]:
    """Update an existing organization."""
    db_organization = await get_organization(db, organization_id)
    if not db_organization:
        return None
    
    update_data = organization_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_organization, field, value)
    
    await db.commit()
    await db.refresh(db_organization)
    return db_organization


async def delete_organization(db: AsyncSession, organization_id: int) -> bool:
    """Delete an organization by ID."""
    db_organization = await get_organization(db, organization_id)
    if not db_organization:
        return False
    
    await db.delete(db_organization)
    await db.commit()
    return True


async def get_organization_by_name(db: AsyncSession, name: str) -> Optional[Organization]:
    """Get an organization by name (case-insensitive)."""
    result = await db.execute(
        select(Organization).where(func.lower(Organization.name) == name.lower())
    )
    return result.scalar_one_or_none()

