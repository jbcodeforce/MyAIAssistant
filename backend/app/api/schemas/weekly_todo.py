from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class WeeklyTodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the weekly todo")
    description: Optional[str] = Field(None, description="Optional description")
    todo_id: Optional[int] = Field(None, description="Optional link to an existing todo")


class WeeklyTodoCreate(WeeklyTodoBase):
    pass


class WeeklyTodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    todo_id: Optional[int] = None


class WeeklyTodoResponse(WeeklyTodoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeeklyTodoListResponse(BaseModel):
    weekly_todos: list[WeeklyTodoResponse]
    total: int
    skip: int
    limit: int


class AllocationDayMinutes(BaseModel):
    mon: int = Field(0, ge=0, description="Minutes allocated for Monday")
    tue: int = Field(0, ge=0, description="Minutes allocated for Tuesday")
    wed: int = Field(0, ge=0, description="Minutes allocated for Wednesday")
    thu: int = Field(0, ge=0, description="Minutes allocated for Thursday")
    fri: int = Field(0, ge=0, description="Minutes allocated for Friday")
    sat: int = Field(0, ge=0, description="Minutes allocated for Saturday")
    sun: int = Field(0, ge=0, description="Minutes allocated for Sunday")


class AllocationResponse(AllocationDayMinutes):
    id: int
    weekly_todo_id: int
    week_key: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AllocationListResponse(BaseModel):
    allocations: list[AllocationResponse]
    week_key: str
