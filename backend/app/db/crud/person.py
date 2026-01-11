from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Person
from app.api.schemas.person import PersonCreate, PersonEntity


async def create_person(db: AsyncSession, person: PersonCreate) -> Person:
    """Create a new person."""
    db_person = Person(**person.model_dump())
    db.add(db_person)
    await db.commit()
    await db.refresh(db_person)
    return db_person


async def get_person(db: AsyncSession, person_id: int) -> Optional[Person]:
    """Get a person by ID."""
    result = await db.execute(select(Person).where(Person.id == person_id))
    return result.scalar_one_or_none()


async def get_persons(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    organization_id: Optional[int] = None,
) -> tuple[list[Person], int]:
    """Get all persons with pagination and optional filtering."""
    query = select(Person)
    
    if project_id:
        query = query.where(Person.project_id == project_id)
    if organization_id:
        query = query.where(Person.organization_id == organization_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Person.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    persons = list(result.scalars().all())
    
    return persons, total


async def update_person(
    db: AsyncSession,
    person_id: int,
    person_update: PersonEntity
) -> Optional[Person]:
    """Update an existing person."""
    db_person = await get_person(db, person_id)
    if not db_person:
        return None
    
    update_data = person_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_person, field, value)
    
    await db.commit()
    await db.refresh(db_person)
    return db_person


async def delete_person(db: AsyncSession, person_id: int) -> bool:
    """Delete a person by ID."""
    db_person = await get_person(db, person_id)
    if not db_person:
        return False
    
    await db.delete(db_person)
    await db.commit()
    return True


async def get_persons_by_project(
    db: AsyncSession,
    project_id: int,
    skip: int = 0,
    limit: int = 100
) -> tuple[list[Person], int]:
    """Get all persons linked to a specific project."""
    return await get_persons(db, skip=skip, limit=limit, project_id=project_id)


async def get_persons_by_organization(
    db: AsyncSession,
    organization_id: int,
    skip: int = 0,
    limit: int = 100
) -> tuple[list[Person], int]:
    """Get all persons linked to a specific organization."""
    return await get_persons(db, skip=skip, limit=limit, organization_id=organization_id)
