from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AssetEntity(BaseModel):
    """Base asset entity with all fields optional (used for updates)."""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Asset name"
    )
    description: Optional[str] = Field(None, description="Short description of the asset")
    reference_url: Optional[str] = Field(
        None,
        max_length=2048,
        description="URL reference to the asset (code repository, document, etc.)"
    )
    project_id: Optional[int] = Field(None, description="Related project ID")
    todo_id: Optional[int] = Field(None, description="Related task ID")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Flink SQL Helper",
                    "description": "Reusable SQL templates for Flink jobs",
                    "reference_url": "https://github.com/org/flink-sql-helpers"
                }
            ]
        }
    )


class AssetCreate(AssetEntity):
    """Asset creation schema - name and reference_url are required."""
    name: str = Field(..., min_length=1, max_length=255, description="Asset name")
    reference_url: str = Field(
        ...,
        max_length=2048,
        description="URL reference to the asset (code repository, document, etc.)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Flink SQL Helper",
                    "description": "Reusable SQL templates for Flink jobs",
                    "reference_url": "https://github.com/org/flink-sql-helpers",
                    "project_id": 1
                }
            ]
        }
    )


class AssetResponse(AssetEntity):
    """Asset response with server-generated fields."""
    id: int
    name: str  # Always present in response
    reference_url: str  # Always present in response
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetListResponse(BaseModel):
    assets: list[AssetResponse]
    total: int
    skip: int
    limit: int

