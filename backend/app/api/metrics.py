from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Project, Todo
from app.api.schemas.metrics import (
    StatusCount,
    ProjectMetrics,
    TaskMetrics,
    TaskCompletionDataPoint,
    TaskCompletionOverTime,
    DashboardMetrics
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


async def get_project_metrics(db: AsyncSession) -> ProjectMetrics:
    """Get project counts grouped by status."""
    # Query projects grouped by status
    query = select(
        Project.status,
        func.count(Project.id).label("count")
    ).group_by(Project.status)
    
    result = await db.execute(query)
    rows = result.all()
    
    by_status = [StatusCount(status=row.status, count=row.count) for row in rows]
    total = sum(s.count for s in by_status)
    
    return ProjectMetrics(total=total, by_status=by_status)


async def get_task_metrics(db: AsyncSession) -> TaskMetrics:
    """Get task (todo) counts grouped by status."""
    query = select(
        Todo.status,
        func.count(Todo.id).label("count")
    ).group_by(Todo.status)
    
    result = await db.execute(query)
    rows = result.all()
    
    by_status = [StatusCount(status=row.status, count=row.count) for row in rows]
    total = sum(s.count for s in by_status)
    
    return TaskMetrics(total=total, by_status=by_status)


async def get_tasks_completion_over_time(
    db: AsyncSession,
    period: str = "daily",
    days: int = 30
) -> TaskCompletionOverTime:
    """Get task completion data over time."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Query completed tasks with completion date
    query = select(
        cast(Todo.completed_at, Date).label("completion_date"),
        func.count(Todo.id).label("count")
    ).where(
        Todo.status == "Completed",
        Todo.completed_at.is_not(None),
        Todo.completed_at >= start_date,
        Todo.completed_at <= end_date
    ).group_by(
        cast(Todo.completed_at, Date)
    ).order_by(
        cast(Todo.completed_at, Date)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    data_points = []
    total_completed = 0
    
    for row in rows:
        date_str = row.completion_date.strftime("%Y-%m-%d") if row.completion_date else ""
        if date_str:
            data_points.append(TaskCompletionDataPoint(date=date_str, count=row.count))
            total_completed += row.count
    
    # For weekly aggregation, group the daily data
    if period == "weekly":
        weekly_data = {}
        for dp in data_points:
            date = datetime.strptime(dp.date, "%Y-%m-%d")
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            weekly_data[week_key] = weekly_data.get(week_key, 0) + dp.count
        
        data_points = [
            TaskCompletionDataPoint(date=k, count=v) 
            for k, v in sorted(weekly_data.items())
        ]
    
    # For monthly aggregation
    elif period == "monthly":
        monthly_data = {}
        for dp in data_points:
            month_key = dp.date[:7]  # YYYY-MM
            monthly_data[month_key] = monthly_data.get(month_key, 0) + dp.count
        
        data_points = [
            TaskCompletionDataPoint(date=f"{k}-01", count=v) 
            for k, v in sorted(monthly_data.items())
        ]
    
    return TaskCompletionOverTime(
        period=period,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        data_points=data_points,
        total_completed=total_completed
    )


@router.get("/projects", response_model=ProjectMetrics)
async def get_projects_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get project metrics grouped by status.
    
    Returns the total number of projects and a breakdown by status
    (Draft, Active, On Hold, Completed, Cancelled).
    """
    return await get_project_metrics(db)


@router.get("/tasks", response_model=TaskMetrics)
async def get_tasks_metrics(db: AsyncSession = Depends(get_db)):
    """
    Get task metrics grouped by status.
    
    Returns the total number of tasks and a breakdown by status
    (Open, Started, Completed, Cancelled).
    """
    return await get_task_metrics(db)


@router.get("/tasks/completion", response_model=TaskCompletionOverTime)
async def get_task_completion_metrics(
    period: str = Query(
        "daily", 
        description="Time period aggregation: daily, weekly, or monthly"
    ),
    days: int = Query(
        30, 
        ge=1, 
        le=365, 
        description="Number of days to look back"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get task completion metrics over time.
    
    Returns the number of tasks completed per day, week, or month
    within the specified time range.
    """
    if period not in ["daily", "weekly", "monthly"]:
        period = "daily"
    
    return await get_tasks_completion_over_time(db, period, days)


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    period: str = Query(
        "daily", 
        description="Time period for completion chart: daily, weekly, or monthly"
    ),
    days: int = Query(
        30, 
        ge=1, 
        le=365, 
        description="Number of days to look back for completion chart"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get combined dashboard metrics.
    
    Returns project metrics, task metrics, and task completion over time
    in a single response for efficient dashboard rendering.
    """
    if period not in ["daily", "weekly", "monthly"]:
        period = "daily"
    
    projects = await get_project_metrics(db)
    tasks = await get_task_metrics(db)
    tasks_completion = await get_tasks_completion_over_time(db, period, days)
    
    return DashboardMetrics(
        projects=projects,
        tasks=tasks,
        tasks_completion=tasks_completion
    )

