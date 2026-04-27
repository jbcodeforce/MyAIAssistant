from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    stakeholders: Optional[str] = Field(None, description="Key stakeholders at the organization")
    team: Optional[str] = Field(None, description="Team members working with this organization")
    # Create/Update: markdown body. Response: file content (source is description_path on disk).
    description: Optional[str] = Field(None, description="Strategy / notes (request body: markdown; response: from file)")
    related_products: Optional[str] = Field(None, description="Products related to this organization")
    is_top_active: bool = Field(False, description="Mark as top-active organization")


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
    is_top_active: Optional[bool] = None

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
    description_path: Optional[str] = Field(
        None,
        description="Path to strategy markdown relative to notes_root (e.g. acme/notes/strategy.md)",
    )

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    organizations: list[OrganizationResponse]
    total: int
    skip: int
    limit: int


class OrganizationExportResponse(BaseModel):
    path: str = Field(
        ...,
        description="Relative path to the exported file, e.g. docs/notes/org-name/full_export.md",
    )
    absolute_path: Optional[str] = Field(None, description="Absolute path on the server (if available)")

