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


class TimeSeriesDataPoint(BaseModel):
    """Generic data point for time series data."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    count: int = Field(..., description="Count for this date")


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


class TimeSeriesMetrics(BaseModel):
    """Generic time series metrics response."""
    period: str = Field(..., description="Time period: daily, weekly, monthly")
    start_date: str = Field(..., description="Start date of the period")
    end_date: str = Field(..., description="End date of the period")
    data_points: list[TimeSeriesDataPoint] = Field(
        default_factory=list, 
        description="List of data points"
    )
    total: int = Field(..., description="Total count in the period")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "period": "daily",
                    "start_date": "2025-12-01",
                    "end_date": "2025-12-31",
                    "data_points": [
                        {"date": "2025-12-01", "count": 2},
                        {"date": "2025-12-02", "count": 1}
                    ],
                    "total": 3
                }
            ]
        }
    )


class StatusTimeSeriesDataPoint(BaseModel):
    """Data point with counts for each status."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    open: int = Field(0, description="Count of open items")
    started: int = Field(0, description="Count of started items")
    completed: int = Field(0, description="Count of completed items")
    cancelled: int = Field(0, description="Count of cancelled items")


class TaskStatusOverTime(BaseModel):
    """Tasks by status over time."""
    period: str = Field(..., description="Time period: daily, weekly, monthly")
    start_date: str = Field(..., description="Start date of the period")
    end_date: str = Field(..., description="End date of the period")
    data_points: list[StatusTimeSeriesDataPoint] = Field(
        default_factory=list,
        description="List of data points with status counts"
    )
    totals: dict[str, int] = Field(
        default_factory=dict,
        description="Total counts per status"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "period": "daily",
                    "start_date": "2025-12-01",
                    "end_date": "2025-12-31",
                    "data_points": [
                        {"date": "2025-12-01", "open": 3, "started": 2, "completed": 1, "cancelled": 0},
                        {"date": "2025-12-02", "open": 2, "started": 3, "completed": 2, "cancelled": 1}
                    ],
                    "totals": {"open": 5, "started": 5, "completed": 3, "cancelled": 1}
                }
            ]
        }
    )


class AssetMetrics(BaseModel):
    """Metrics for assets grouped by status."""
    total: int = Field(..., description="Total number of assets")
    by_status: list[StatusCount] = Field(default_factory=list, description="Assets count per status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total": 12,
                    "by_status": [
                        {"status": "Started", "count": 4},
                        {"status": "Active", "count": 5},
                        {"status": "Completed", "count": 3}
                    ]
                }
            ]
        }
    )


class DashboardMetrics(BaseModel):
    """Combined dashboard metrics response."""
    projects: ProjectMetrics = Field(..., description="Project metrics")
    tasks: TaskMetrics = Field(..., description="Task metrics")
    assets: AssetMetrics = Field(..., description="Asset metrics")
    tasks_completion: TaskCompletionOverTime = Field(..., description="Task completion over time")
    task_status_over_time: TaskStatusOverTime = Field(..., description="Task status changes over time")
    organizations_created: TimeSeriesMetrics = Field(..., description="Organizations created over time")
    meetings_created: TimeSeriesMetrics = Field(..., description="Meetings created over time")
    
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
                    },
                    "task_status_over_time": {
                        "period": "daily",
                        "start_date": "2025-12-01",
                        "end_date": "2025-12-31",
                        "data_points": [
                            {"date": "2025-12-01", "open": 3, "started": 2, "completed": 1, "cancelled": 0}
                        ],
                        "totals": {"open": 3, "started": 2, "completed": 1, "cancelled": 0}
                    },
                    "organizations_created": {
                        "period": "daily",
                        "start_date": "2025-12-01",
                        "end_date": "2025-12-31",
                        "data_points": [
                            {"date": "2025-12-01", "count": 1}
                        ],
                        "total": 1
                    },
                    "meetings_created": {
                        "period": "daily",
                        "start_date": "2025-12-01",
                        "end_date": "2025-12-31",
                        "data_points": [
                            {"date": "2025-12-01", "count": 2}
                        ],
                        "total": 2
                    }
                }
            ]
        }
    )

