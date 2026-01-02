from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.project import (
    ProjectCreate,
    ProjectEntity,
    ProjectResponse,
    ProjectListResponse,
)
from app.api.schemas.todo import TodoListResponse


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project.
    """
    # Verify organization exists if organization_id is provided
    if project.organization_id:
        organization = await crud.get_organization(db=db, organization_id=project.organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
    
    return await crud.create_project(db=db, project=project)


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of projects with optional filtering.
    """
    projects, total = await crud.get_projects(
        db=db,
        skip=skip,
        limit=limit,
        organization_id=organization_id,
        status=status
    )
    return ProjectListResponse(projects=projects, total=total, skip=skip, limit=limit)


@router.get("/search/by-name", response_model=ProjectResponse)
async def get_project_by_name(
    name: str = Query(..., description="Project name to search for (case-insensitive)"),
    organization_id: int = Query(..., description="Organization ID the project belongs to"),
    db: AsyncSession = Depends(get_db)
):
    """
    Find a project by name and organization ID (case-insensitive exact match).
    """
    project = await crud.get_project_by_name_and_organization(
        db=db, name=name, organization_id=organization_id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific project by ID.
    """
    project = await crud.get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectEntity,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a project.
    """
    # Verify organization exists if organization_id is being updated
    if project_update.organization_id is not None:
        organization = await crud.get_organization(db=db, organization_id=project_update.organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if trying to complete the project
    if project_update.status == "Completed":
        active_todos_count = await crud.count_active_todos_for_project(db=db, project_id=project_id)
        if active_todos_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete project: {active_todos_count} active task(s) still associated with this project"
            )
    
    project = await crud.update_project(
        db=db, project_id=project_id, project_update=project_update
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a project.
    """
    success = await crud.delete_project(db=db, project_id=project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None


@router.get("/{project_id}/todos", response_model=TodoListResponse)
async def list_project_todos(
    project_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all todos linked to a specific project.
    """
    # Verify project exists
    project = await crud.get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    todos, total = await crud.get_todos_by_project(
        db=db, project_id=project_id, skip=skip, limit=limit
    )
    return TodoListResponse(todos=todos, total=total, skip=skip, limit=limit)
