from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    stakeholders: Optional[str] = Field(None, description="Key stakeholders at the organization")
    team: Optional[str] = Field(None, description="Team members working with this organization")
    description: Optional[str] = Field(None, description="Organization strategy and notes")
    related_products: Optional[str] = Field(None, description="Products related to this organization")


class OrganizationCreate(OrganizationBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Acme Corporation",
                    "stakeholders": "John Doe (CTO), Jane Smith (PM)",
                    "team": "Alice, Bob",
                    "description": "Enterprise organization focused on cloud migration",
                    "related_products": "Platform API, Analytics Dashboard"
                }
            ]
        }
    )


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    stakeholders: Optional[str] = None
    team: Optional[str] = None
    description: Optional[str] = None
    related_products: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "description": "Updated organization strategy notes"
                }
            ]
        }
    )


class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    organizations: list[OrganizationResponse]
    total: int
    skip: int
    limit: int

