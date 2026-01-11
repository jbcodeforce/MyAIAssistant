from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class PersonEntity(BaseModel):
    """Base person entity with all fields optional (used for updates)."""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Person's name"
    )
    context: Optional[str] = Field(
        None,
        description="Context about the relationship or how you know this person"
    )
    role: Optional[str] = Field(
        None,
        max_length=255,
        description="Person's role or title"
    )
    last_met_date: Optional[datetime] = Field(
        None,
        description="Date when you last met or interacted with this person"
    )
    next_step: Optional[str] = Field(
        None,
        description="Next planned action or follow-up with this person"
    )
    project_id: Optional[int] = Field(
        None,
        description="Related project ID"
    )
    organization_id: Optional[int] = Field(
        None,
        description="Related organization ID"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "John Smith",
                    "context": "Technical lead on the migration project",
                    "role": "Engineering Manager",
                    "last_met_date": "2026-01-05T14:00:00",
                    "next_step": "Schedule follow-up meeting to discuss timeline"
                }
            ]
        }
    )


class PersonCreate(PersonEntity):
    """Person creation schema - name is required."""
    name: str = Field(..., min_length=1, max_length=255, description="Person's name")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Jane Doe",
                    "context": "Product manager for platform team",
                    "role": "Senior Product Manager",
                    "project_id": 1,
                    "organization_id": 2,
                    "next_step": "Send requirements document for review"
                }
            ]
        }
    )


class PersonResponse(PersonEntity):
    """Person response with server-generated fields."""
    id: int
    name: str  # Always present in response
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonListResponse(BaseModel):
    persons: list[PersonResponse]
    total: int
    skip: int
    limit: int
