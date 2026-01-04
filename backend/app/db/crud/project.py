from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project
from app.api.schemas.project import ProjectCreate, ProjectEntity


async def create_project(db: AsyncSession, project: ProjectCreate) -> Project:
    """Create a new project."""
    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


async def get_project(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Get a project by ID."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def get_projects(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    organization_id: Optional[int] = None,
    status: Optional[str] = None,
) -> tuple[list[Project], int]:
    """Get all projects with pagination and optional filtering."""
    query = select(Project)
    
    if organization_id:
        query = query.where(Project.organization_id == organization_id)
    if status:
        # Support comma-separated status values
        status_list = [s.strip() for s in status.split(',')]
        if len(status_list) == 1:
            query = query.where(Project.status == status_list[0])
        else:
            query = query.where(Project.status.in_(status_list))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    projects = list(result.scalars().all())
    
    return projects, total


async def update_project(
    db: AsyncSession,
    project_id: int,
    project_update: ProjectEntity
) -> Optional[Project]:
    """Update an existing project."""
    db_project = await get_project(db, project_id)
    if not db_project:
        return None
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    await db.commit()
    await db.refresh(db_project)
    return db_project


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    """Delete a project by ID."""
    db_project = await get_project(db, project_id)
    if not db_project:
        return False
    
    await db.delete(db_project)
    await db.commit()
    return True


async def get_project_by_name_and_organization(
    db: AsyncSession,
    name: str,
    organization_id: int
) -> Optional[Project]:
    """Get a project by name and organization ID."""
    result = await db.execute(
        select(Project).where(
            func.lower(Project.name) == name.lower(),
            Project.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()

