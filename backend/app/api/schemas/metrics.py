from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class StatusCount(BaseModel):
    """Count for a specific status."""
    status: str = Field(..., description="Status name")
    count: int = Field(..., description="Number of items with this status")


class ProjectMetrics(BaseModel):
    """Metrics for projects grouped by status."""
    total: int = Field(..., description="Total number of projects")
    by_status: list[StatusCount] = Field(default_factory=list, description="Projects count per status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 15,
                    "by_status": [
                        {"status": "Draft", "count": 3},
                        {"status": "Active", "count": 5},
                        {"status": "On Hold", "count": 2},
                        {"status": "Completed", "count": 4},
                        {"status": "Cancelled", "count": 1}
                    ]
                }
            ]
        }
    )


class TaskMetrics(BaseModel):
    """Metrics for tasks (todos) grouped by status."""
    total: int = Field(..., description="Total number of tasks")
    by_status: list[StatusCount] = Field(default_factory=list, description="Tasks count per status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 42,
                    "by_status": [
                        {"status": "Open", "count": 15},
                        {"status": "Started", "count": 8},
                        {"status": "Completed", "count": 17},
                        {"status": "Cancelled", "count": 2}
                    ]
                }
            ]
        }
    )


class TaskCompletionDataPoint(BaseModel):
    """Single data point for task completion over time."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    count: int = Field(..., description="Number of tasks completed on this date")


class TaskCompletionOverTime(BaseModel):
    """Tasks completed over a time period."""
    period: str = Field(..., description="Time period: daily, weekly, monthly")
    start_date: str = Field(..., description="Start date of the period")
    end_date: str = Field(..., description="End date of the period")
    data_points: list[TaskCompletionDataPoint] = Field(
        default_factory=list, 
        description="List of completion data points"
    )
    total_completed: int = Field(..., description="Total tasks completed in the period")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "period": "daily",
                    "start_date": "2025-12-01",
                    "end_date": "2025-12-31",
                    "data_points": [
                        {"date": "2025-12-01", "count": 3},
                        {"date": "2025-12-02", "count": 5},
                        {"date": "2025-12-03", "count": 2}
                    ],
                    "total_completed": 10
                }
            ]
        }
    )


class DashboardMetrics(BaseModel):
    """Combined dashboard metrics response."""
    projects: ProjectMetrics = Field(..., description="Project metrics")
    tasks: TaskMetrics = Field(..., description="Task metrics")
    tasks_completion: TaskCompletionOverTime = Field(..., description="Task completion over time")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "projects": {
                        "total": 15,
                        "by_status": [
                            {"status": "Draft", "count": 3},
                            {"status": "Active", "count": 5}
                        ]
                    },
                    "tasks": {
                        "total": 42,
                        "by_status": [
                            {"status": "Open", "count": 15},
                            {"status": "Completed", "count": 17}
                        ]
                    },
                    "tasks_completion": {
                        "period": "daily",
                        "start_date": "2025-12-01",
                        "end_date": "2025-12-31",
                        "data_points": [
                            {"date": "2025-12-01", "count": 3}
                        ],
                        "total_completed": 3
                    }
                }
            ]
        }
    )

