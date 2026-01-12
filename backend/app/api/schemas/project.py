from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class Step(BaseModel):
    """A step with action and assignee."""
    what: str = Field(..., description="Description of the step/action")
    who: str = Field(..., description="Person responsible for this step")


class ProjectEntity(BaseModel):
    """Base project entity with all fields optional (used for updates)."""
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Project name"
    )
    description: Optional[str] = Field(None, description="Project description")
    organization_id: Optional[int] = Field(None, description="Related organization ID")
    status: Optional[str] = Field(
        None,
        description="Project status: Draft, Active, On Hold, Completed, Cancelled"
    )
    tasks: Optional[str] = Field(
        None,
        description="Bullet list of small tasks (markdown format)"
    )
    past_steps: Optional[list[Step]] = Field(
        None,
        description="Past steps taken to address the project's challenges"
    )
    next_steps: Optional[list[Step]] = Field(
        None,
        description="Next steps planned to move the project forward"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "Active",
                    "tasks": "- Review requirements\n- Setup environment\n- Run migration",
                    "past_steps": [
                        {"what": "Completed initial analysis", "who": "John"},
                        {"what": "Met with stakeholders", "who": "Jane"}
                    ],
                    "next_steps": [
                        {"what": "Finalize design", "who": "John"},
                        {"what": "Begin implementation", "who": "Team"}
                    ]
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
                    "description": "Migrate organization to new platform version",
                    "organization_id": 1,
                    "status": "Active",
                    "tasks": "- Review requirements\n- Setup environment\n- Run migration",
                    "past_steps": [
                        {"what": "Completed initial analysis", "who": "John"},
                        {"what": "Met with stakeholders", "who": "Jane"}
                    ],
                    "next_steps": [
                        {"what": "Finalize design", "who": "John"},
                        {"what": "Begin implementation", "who": "Team"}
                    ]
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
