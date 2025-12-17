from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProjectEntity(BaseModel):
    """Base project entity with all fields optional (used for updates)."""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Project name"
    )
    description: Optional[str] = Field(None, description="Project description")
    customer_id: Optional[int] = Field(None, description="Related customer ID")
    status: Optional[str] = Field(
        None,
        description="Project status: Draft, Active, On Hold, Completed, Cancelled"
    )
    tasks: Optional[str] = Field(
        None,
        description="Bullet list of small tasks (markdown format)"
    )
    past_steps: Optional[str] = Field(
        None,
        description="Past steps taken to address the project's challenges"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "Active",
                    "tasks": "- Review requirements\n- Setup environment\n- Run migration",
                    "past_steps": "- Review requirements\n- Setup environment\n- Run migration"
                }
            ]
        }
    )


class ProjectCreate(ProjectEntity):
    """Project creation schema - name is required."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    status: str = Field(
        default="Draft",
        description="Project status: Draft, Active, On Hold, Completed, Cancelled"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Q1 Platform Migration",
                    "description": "Migrate customer to new platform version",
                    "customer_id": 1,
                    "status": "Active",
                    "tasks": "- Review requirements\n- Setup environment\n- Run migration",
                    "past_steps": "- Review requirements\n- Setup environment\n- Run migration"             
                }
            ]
        }
    )


class ProjectResponse(ProjectEntity):
    """Project response with server-generated fields."""
    id: int
    name: str  # Always present in response
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
    skip: int
    limit: int

