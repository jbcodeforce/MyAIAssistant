from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class TaskPlanBase(BaseModel):
    content: str = Field(..., min_length=1, description="Markdown content of the task plan")


class TaskPlanCreate(TaskPlanBase):
    todo_id: int = Field(..., description="ID of the associated todo")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "todo_id": 1,
                    "content": "## Approach\n\n1. First step\n2. Second step\n3. Third step"
                }
            ]
        }
    )


class TaskPlanUpdate(BaseModel):
    content: str = Field(..., min_length=1, description="Updated markdown content")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "content": "## Updated Plan\n\n1. New first step\n2. New second step"
                }
            ]
        }
    )


class TaskPlanResponse(TaskPlanBase):
    id: int
    todo_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

