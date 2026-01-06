from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.asset import (
    AssetCreate,
    AssetEntity,
    AssetResponse,
    AssetListResponse,
)


router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/", response_model=AssetResponse, status_code=201)
async def create_asset(
    asset: AssetCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new asset.
    """
    # Verify project exists if project_id is provided
    if asset.project_id:
        project = await crud.get_project(db=db, project_id=asset.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify todo exists if todo_id is provided
    if asset.todo_id:
        todo = await crud.get_todo(db=db, todo_id=asset.todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
    
    return await crud.create_asset(db=db, asset=asset)


@router.get("/", response_model=AssetListResponse)
async def list_assets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    todo_id: Optional[int] = Query(None, description="Filter by todo ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of assets with optional filtering.
    """
    assets, total = await crud.get_assets(
        db=db,
        skip=skip,
        limit=limit,
        project_id=project_id,
        todo_id=todo_id
    )
    return AssetListResponse(assets=assets, total=total, skip=skip, limit=limit)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific asset by ID.
    """
    asset = await crud.get_asset(db=db, asset_id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_update: AssetEntity,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an asset.
    """
    # Verify project exists if project_id is being updated
    if asset_update.project_id is not None:
        project = await crud.get_project(db=db, project_id=asset_update.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify todo exists if todo_id is being updated
    if asset_update.todo_id is not None:
        todo = await crud.get_todo(db=db, todo_id=asset_update.todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
    
    asset = await crud.update_asset(
        db=db, asset_id=asset_id, asset_update=asset_update
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an asset.
    """
    success = await crud.delete_asset(db=db, asset_id=asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return None

