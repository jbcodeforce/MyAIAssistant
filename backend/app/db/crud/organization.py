from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Organization
from app.api.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services.organization_notes import default_description_path, write_description


async def create_organization(db: AsyncSession, organization: OrganizationCreate) -> Organization:
    """
    Create a new organization. API field `description` is markdown content; the database stores
    `description_path` (relative to notes_root); the file is written by the API after insert.
    """
    data = organization.model_dump()
    content = data.pop("description", None)
    if content and str(content).strip():
        data["description_path"] = default_description_path(data["name"])
    else:
        data["description_path"] = None
    db_organization = Organization(**data)
    db.add(db_organization)
    await db.commit()
    await db.refresh(db_organization)
    if db_organization.description_path and content and str(content).strip():
        write_description(db_organization.name, db_organization.description_path, str(content).strip())
    return db_organization


async def get_organization(db: AsyncSession, organization_id: int) -> Optional[Organization]:
    """Get an organization by ID."""
    result = await db.execute(select(Organization).where(Organization.id == organization_id))
    return result.scalar_one_or_none()


async def get_organizations(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    top_active: Optional[bool] = None,
) -> tuple[list[Organization], int]:
    """Get all organizations with pagination. Optionally filter by top_active."""
    query = select(Organization)
    if top_active is not None:
        query = query.where(Organization.is_top_active == (1 if top_active else 0))

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
    """Update an existing organization. The `description` key (markdown content) is not a DB field."""
    db_organization = await get_organization(db, organization_id)
    if not db_organization:
        return None

    update_data = organization_update.model_dump(exclude_unset=True)
    update_data.pop("description", None)
    for field, value in update_data.items():
        if hasattr(db_organization, field):
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

