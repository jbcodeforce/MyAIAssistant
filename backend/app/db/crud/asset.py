from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Asset
from app.api.schemas.asset import AssetCreate, AssetEntity


async def create_asset(db: AsyncSession, asset: AssetCreate) -> Asset:
    """Create a new asset."""
    db_asset = Asset(**asset.model_dump())
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset


async def get_asset(db: AsyncSession, asset_id: int) -> Optional[Asset]:
    """Get an asset by ID."""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    return result.scalar_one_or_none()


async def get_assets(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    todo_id: Optional[int] = None,
    status: Optional[str] = None,
) -> tuple[list[Asset], int]:
    """Get all assets with pagination and optional filtering."""
    query = select(Asset)
    
    if project_id is not None:
        query = query.where(Asset.project_id == project_id)
    if todo_id is not None:
        query = query.where(Asset.todo_id == todo_id)
    if status is not None:
        query = query.where(Asset.status == status)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    assets = list(result.scalars().all())
    
    return assets, total


async def update_asset(
    db: AsyncSession,
    asset_id: int,
    asset_update: AssetEntity
) -> Optional[Asset]:
    """Update an existing asset."""
    db_asset = await get_asset(db, asset_id)
    if not db_asset:
        return None
    
    update_data = asset_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_asset, field, value)
    
    await db.commit()
    await db.refresh(db_asset)
    return db_asset


async def delete_asset(db: AsyncSession, asset_id: int) -> bool:
    """Delete an asset by ID."""
    db_asset = await get_asset(db, asset_id)
    if not db_asset:
        return False
    
    await db.delete(db_asset)
    await db.commit()
    return True


async def get_assets_by_project(
    db: AsyncSession,
    project_id: int,
    skip: int = 0,
    limit: int = 100
) -> tuple[list[Asset], int]:
    """Get all assets for a specific project."""
    return await get_assets(db, skip=skip, limit=limit, project_id=project_id)


async def get_assets_by_todo(
    db: AsyncSession,
    todo_id: int,
    skip: int = 0,
    limit: int = 100
) -> tuple[list[Asset], int]:
    """Get all assets for a specific todo."""
    return await get_assets(db, skip=skip, limit=limit, todo_id=todo_id)

