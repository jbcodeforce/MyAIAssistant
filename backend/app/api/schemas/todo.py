from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the todo")
    description: Optional[str] = Field(None, description="Detailed description of the todo")
    status: str = Field(default="Open", description="Status: Open, Started, Completed, Cancelled")
    urgency: Optional[str] = Field(None, description="Urgency level: Urgent, Not Urgent")
    importance: Optional[str] = Field(None, description="Importance level: Important, Not Important")
    category: Optional[str] = Field(None, max_length=100, description="Category for grouping todos")
    project_id: Optional[int] = Field(None, description="Related project ID")
    due_date: Optional[datetime] = Field(None, description="Due date for the todo")
    source_type: Optional[str] = Field(None, max_length=50, description="Source type (e.g., meeting, knowledge)")
    source_id: Optional[int] = Field(None, description="Source reference ID")


class TodoCreate(TodoBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Review project documentation",
                    "description": "Review and update the project documentation for the new release",
                    "status": "Open",
                    "urgency": "Urgent",
                    "importance": "Important",
                    "category": "Documentation",
                    "due_date": "2025-12-15T10:00:00"
                }
            ]
        }
    )


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    urgency: Optional[str] = None
    importance: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    project_id: Optional[int] = None
    due_date: Optional[datetime] = None
    source_type: Optional[str] = Field(None, max_length=50)
    source_id: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "Started",
                    "urgency": "Urgent"
                }
            ]
        }
    )


class TodoResponse(TodoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TodoListResponse(BaseModel):
    todos: list[TodoResponse]
    total: int
    skip: int
    limit: int

