from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class Dimension(BaseModel):
    """A life dimension with importance and time spent ratings."""
    importance: int = Field(..., ge=0, le=10, description="Importance rating (0-10)")
    time_spent: int = Field(..., ge=0, le=10, description="Time spent rating (0-10)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"importance": 8, "time_spent": 5}
            ]
        }
    )


class SLPassessmentEntity(BaseModel):
    """Base SLP assessment entity with all fields optional (used for updates)."""
    partner: Optional[Dimension] = Field(None, description="Partner relationship dimension")
    family: Optional[Dimension] = Field(None, description="Family relationships dimension")
    friends: Optional[Dimension] = Field(None, description="Friendships dimension")
    physical_health: Optional[Dimension] = Field(None, description="Physical health dimension")
    mental_health: Optional[Dimension] = Field(None, description="Mental health dimension")
    spirituality: Optional[Dimension] = Field(None, description="Spirituality dimension")
    community: Optional[Dimension] = Field(None, description="Community involvement dimension")
    societal: Optional[Dimension] = Field(None, description="Societal contribution dimension")
    job_task: Optional[Dimension] = Field(None, description="Job/work tasks dimension")
    learning: Optional[Dimension] = Field(None, description="Learning and growth dimension")
    finance: Optional[Dimension] = Field(None, description="Financial management dimension")
    hobbies: Optional[Dimension] = Field(None, description="Hobbies dimension")
    online_entertainment: Optional[Dimension] = Field(None, description="Online entertainment dimension")
    offline_entertainment: Optional[Dimension] = Field(None, description="Offline entertainment dimension")
    physiological_needs: Optional[Dimension] = Field(None, description="Physiological needs dimension")
    daily_activities: Optional[Dimension] = Field(None, description="Daily activities dimension")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "partner": {"importance": 9, "time_spent": 6},
                    "family": {"importance": 8, "time_spent": 5}
                }
            ]
        }
    )


class SLPassessmentCreate(BaseModel):
    """SLP assessment creation schema - all dimensions are required."""
    partner: Dimension = Field(..., description="Partner relationship dimension")
    family: Dimension = Field(..., description="Family relationships dimension")
    friends: Dimension = Field(..., description="Friendships dimension")
    physical_health: Dimension = Field(..., description="Physical health dimension")
    mental_health: Dimension = Field(..., description="Mental health dimension")
    spirituality: Dimension = Field(..., description="Spirituality dimension")
    community: Dimension = Field(..., description="Community involvement dimension")
    societal: Dimension = Field(..., description="Societal contribution dimension")
    job_task: Dimension = Field(..., description="Job/work tasks dimension")
    learning: Dimension = Field(..., description="Learning and growth dimension")
    finance: Dimension = Field(..., description="Financial management dimension")
    hobbies: Dimension = Field(..., description="Hobbies dimension")
    online_entertainment: Dimension = Field(..., description="Online entertainment dimension")
    offline_entertainment: Dimension = Field(..., description="Offline entertainment dimension")
    physiological_needs: Dimension = Field(..., description="Physiological needs dimension")
    daily_activities: Dimension = Field(..., description="Daily activities dimension")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "partner": {"importance": 9, "time_spent": 6},
                    "family": {"importance": 8, "time_spent": 5},
                    "friends": {"importance": 7, "time_spent": 4},
                    "physical_health": {"importance": 9, "time_spent": 7},
                    "mental_health": {"importance": 9, "time_spent": 6},
                    "spirituality": {"importance": 5, "time_spent": 3},
                    "community": {"importance": 6, "time_spent": 2},
                    "societal": {"importance": 5, "time_spent": 1},
                    "job_task": {"importance": 8, "time_spent": 9},
                    "learning": {"importance": 8, "time_spent": 5},
                    "finance": {"importance": 7, "time_spent": 3},
                    "hobbies": {"importance": 7, "time_spent": 4},
                    "online_entertainment": {"importance": 4, "time_spent": 6},
                    "offline_entertainment": {"importance": 6, "time_spent": 3},
                    "physiological_needs": {"importance": 8, "time_spent": 7},
                    "daily_activities": {"importance": 6, "time_spent": 5}
                }
            ]
        }
    )


class SLPassessmentResponse(BaseModel):
    """SLP assessment response with server-generated fields."""
    id: int
    partner: Dimension
    family: Dimension
    friends: Dimension
    physical_health: Dimension
    mental_health: Dimension
    spirituality: Dimension
    community: Dimension
    societal: Dimension
    job_task: Dimension
    learning: Dimension
    finance: Dimension
    hobbies: Dimension
    online_entertainment: Dimension
    offline_entertainment: Dimension
    physiological_needs: Dimension
    daily_activities: Dimension
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SLPassessmentListResponse(BaseModel):
    """Response for listing SLP assessments with pagination."""
    assessments: list[SLPassessmentResponse]
    total: int
    skip: int
    limit: int

