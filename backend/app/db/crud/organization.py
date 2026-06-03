from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Organization
from app.api.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.db.errors import DuplicateOrganizationError
from app.services.organization_notes import default_description_path, write_description


def _name_lower_match(name: str):
    return func.lower(Organization.name) == name.lower()


async def find_organization_by_name(
    db: AsyncSession,
    name: str,
    *,
    exclude_id: Optional[int] = None,
) -> Optional[Organization]:
    """Find an organization by case-insensitive name, optionally excluding one id."""
    query = select(Organization).where(_name_lower_match(name))
    if exclude_id is not None:
        query = query.where(Organization.id != exclude_id)
    query = query.order_by(Organization.id.asc()).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_organization(db: AsyncSession, organization: OrganizationCreate) -> Organization:
    """
    Create a new organization. API field `description` is markdown content; the database stores
    `description_path` (relative to notes_root); the file is written by the API after insert.
    """
    if await find_organization_by_name(db, organization.name):
        raise DuplicateOrganizationError(organization.name)

    data = organization.model_dump()
    content = data.pop("description", None)
    if content and str(content).strip():
        data["description_path"] = default_description_path(data["name"])
    else:
        data["description_path"] = None
    db_organization = Organization(**data)
    db.add(db_organization)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DuplicateOrganizationError(organization.name) from exc
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

    new_name = update_data.get("name")
    if new_name is not None and new_name.lower() != db_organization.name.lower():
        if await find_organization_by_name(db, new_name, exclude_id=organization_id):
            raise DuplicateOrganizationError(new_name)

    for field, value in update_data.items():
        if hasattr(db_organization, field):
            setattr(db_organization, field, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        conflict_name = new_name if new_name is not None else db_organization.name
        raise DuplicateOrganizationError(conflict_name) from exc
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
    """Get an organization by name (case-insensitive). Returns lowest id if legacy duplicates exist."""
    return await find_organization_by_name(db, name)
