from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationListResponse,
)


router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    organization: OrganizationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new organization.
    """
    return await crud.create_organization(db=db, organization=organization)


@router.get("/", response_model=OrganizationListResponse)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of organizations with pagination.
    """
    organizations, total = await crud.get_organizations(db=db, skip=skip, limit=limit)
    return OrganizationListResponse(organizations=organizations, total=total, skip=skip, limit=limit)


@router.get("/search/by-name", response_model=OrganizationResponse)
async def get_organization_by_name(
    name: str = Query(..., description="Organization name to search for (case-insensitive)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Find an organization by name (case-insensitive exact match).
    """
    organization = await crud.get_organization_by_name(db=db, name=name)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific organization by ID.
    """
    organization = await crud.get_organization(db=db, organization_id=organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    organization_update: OrganizationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an organization.
    """
    organization = await crud.update_organization(
        db=db, organization_id=organization_id, organization_update=organization_update
    )
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.delete("/{organization_id}", status_code=204)
async def delete_organization(
    organization_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an organization.
    """
    success = await crud.delete_organization(db=db, organization_id=organization_id)
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")
    return None

