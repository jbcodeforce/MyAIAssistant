from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.settings import (
    SettingsUpdate,
    SettingsResponse,
    SettingsResponseSafe,
)


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=SettingsResponseSafe)
async def get_settings(
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve application settings.
    Returns settings without sensitive fields (api_key is excluded).
    Creates default settings if none exist.
    """
    settings = await crud.get_or_create_settings(db)
    return settings


@router.get("/full", response_model=SettingsResponse)
async def get_settings_full(
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve application settings including sensitive fields.
    Use with caution - returns api_key.
    Creates default settings if none exist.
    """
    settings = await crud.get_or_create_settings(db)
    return settings


@router.put("/", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update application settings.
    Only provided fields will be updated; others remain unchanged.
    Creates default settings if none exist before updating.
    """
    # Ensure settings exist before updating
    await crud.get_or_create_settings(db)
    
    updated_settings = await crud.update_settings(db, settings_update)
    return updated_settings

