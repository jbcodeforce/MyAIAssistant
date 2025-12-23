from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Todo, Knowledge, TaskPlan, Organization, Project, Settings
from app.api.schemas.todo import TodoCreate, TodoUpdate
from app.api.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate
from app.api.schemas.task_plan import TaskPlanCreate, TaskPlanUpdate
from app.api.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.api.schemas.project import ProjectCreate, ProjectEntity
from app.api.schemas.settings import SettingsCreate, SettingsUpdate
from app.core.config import get_settings

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


# TaskPlan CRUD operations

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


# Organization CRUD operations

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


# Project CRUD operations

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


async def get_todos_by_project(
    db: AsyncSession,
    project_id: int,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Todo], int]:
    """Get all todos for a specific project."""
    query = select(Todo).where(Todo.project_id == project_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Todo.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    todos = list(result.scalars().all())
    
    return todos, total


# Settings CRUD operations

async def get_settings_from_db(db: AsyncSession) -> Optional[Settings]:
    """Get the application settings (singleton pattern - only one row)."""
    result = await db.execute(select(Settings).limit(1))
    return result.scalar_one_or_none()


async def create_settings(db: AsyncSession, settings: SettingsCreate) -> Settings:
    """Create application settings (should only be called once)."""
    db_settings = Settings(**settings.model_dump(exclude_unset=True))
    db.add(db_settings)
    await db.commit()
    await db.refresh(db_settings)
    return db_settings


async def update_settings(
    db: AsyncSession,
    settings_update: SettingsUpdate
) -> Optional[Settings]:
    """Update application settings."""
    db_settings = await get_settings_from_db(db)
    if not db_settings:
        return None
    
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_settings, field, value)
    
    await db.commit()
    await db.refresh(db_settings)
    return db_settings


async def get_or_create_settings(db: AsyncSession) -> Settings:
    """Get existing settings or create default settings if none exist."""
    settings = await get_settings_from_db(db)
    if settings:
        return settings
    app_settings = get_settings()
    default_settings = SettingsCreate(
        llm_name=app_settings.llm_model,
        llm_api_endpoint=app_settings.llm_base_url,
        api_key=app_settings.llm_api_key,
        default_temperature=app_settings.llm_temperature,
        chunk_size=app_settings.chunk_size,
        overlap=app_settings.overlap,
        min_chunk_size=app_settings.min_chunk_size)
    return await create_settings(db, default_settings)
