from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.person import (
    PersonCreate,
    PersonEntity,
    PersonResponse,
    PersonListResponse,
)


router = APIRouter(prefix="/persons", tags=["persons"])


@router.post("/", response_model=PersonResponse, status_code=201)
async def create_person(
    person: PersonCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new person.
    """
    # Verify project exists if project_id is provided
    if person.project_id:
        project = await crud.get_project(db=db, project_id=person.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify organization exists if organization_id is provided
    if person.organization_id:
        organization = await crud.get_organization(db=db, organization_id=person.organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
    
    return await crud.create_person(db=db, person=person)


@router.get("/", response_model=PersonListResponse)
async def list_persons(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of persons with optional filtering.
    """
    persons, total = await crud.get_persons(
        db=db,
        skip=skip,
        limit=limit,
        project_id=project_id,
        organization_id=organization_id
    )
    return PersonListResponse(persons=persons, total=total, skip=skip, limit=limit)


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific person by ID.
    """
    person = await crud.get_person(db=db, person_id=person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: int,
    person_update: PersonEntity,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a person.
    """
    # Verify project exists if project_id is being updated
    if person_update.project_id is not None:
        project = await crud.get_project(db=db, project_id=person_update.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify organization exists if organization_id is being updated
    if person_update.organization_id is not None:
        organization = await crud.get_organization(db=db, organization_id=person_update.organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
    
    person = await crud.update_person(
        db=db, person_id=person_id, person_update=person_update
    )
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.delete("/{person_id}", status_code=204)
async def delete_person(
    person_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a person.
    """
    success = await crud.delete_person(db=db, person_id=person_id)
    if not success:
        raise HTTPException(status_code=404, detail="Person not found")
    return None
