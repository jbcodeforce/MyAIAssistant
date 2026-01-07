from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Project, Todo, Organization, MeetingRef, Asset
from app.api.schemas.metrics import (
    StatusCount,
    ProjectMetrics,
    TaskMetrics,
    AssetMetrics,
    TaskCompletionDataPoint,
    TaskCompletionOverTime,
    TimeSeriesDataPoint,
    TimeSeriesMetrics,
    StatusTimeSeriesDataPoint,
    TaskStatusOverTime,
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


async def get_asset_metrics(db: AsyncSession) -> AssetMetrics:
    """Get asset counts grouped by status and total usage."""
    # Query assets grouped by status
    status_query = select(
        Asset.status,
        func.count(Asset.id).label("count")
    ).group_by(Asset.status)
    
    result = await db.execute(status_query)
    rows = result.all()
    
    by_status = [StatusCount(status=row.status, count=row.count) for row in rows]
    total = sum(s.count for s in by_status)
    
    # Query total usage (sum of all project_count values)
    usage_query = select(func.coalesce(func.sum(Asset.project_count), 0))
    usage_result = await db.execute(usage_query)
    total_usage = usage_result.scalar() or 0
    
    return AssetMetrics(total=total, total_usage=total_usage, by_status=by_status)


async def get_tasks_completion_over_time(
    db: AsyncSession,
    period: str = "daily",
    days: int = 30
) -> TaskCompletionOverTime:
    """Get task completion data over time."""
    # Add 1 day buffer to end_date to handle UTC vs local timezone differences
    end_date = datetime.now() + timedelta(days=1)
    start_date = datetime.now() - timedelta(days=days)
    
    # Query completed tasks with completion date
    query = select(
        func.date(Todo.completed_at).label("completion_date"),
        func.count(Todo.id).label("count")
    ).where(
        Todo.status == "Completed",
        Todo.completed_at.is_not(None),
        Todo.completed_at >= start_date,
        Todo.completed_at <= end_date
    ).group_by(
        func.date(Todo.completed_at)
    ).order_by(
        func.date(Todo.completed_at)
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


async def get_organizations_over_time(
    db: AsyncSession,
    period: str = "daily",
    days: int = 30
) -> TimeSeriesMetrics:
    """Get organizations created over time."""
    # Add 1 day buffer to end_date to handle UTC vs local timezone differences
    end_date = datetime.now() + timedelta(days=1)
    start_date = datetime.now() - timedelta(days=days)
    
    query = select(
        func.date(Organization.created_at).label("created_date"),
        func.count(Organization.id).label("count")
    ).where(
        Organization.created_at >= start_date,
        Organization.created_at <= end_date
    ).group_by(
        func.date(Organization.created_at)
    ).order_by(
        func.date(Organization.created_at)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    data_points = []
    total = 0
    
    for row in rows:
        # Handle both date objects and strings (SQLite returns strings)
        if row.created_date:
            if hasattr(row.created_date, 'strftime'):
                date_str = row.created_date.strftime("%Y-%m-%d")
            else:
                date_str = str(row.created_date)[:10]
        else:
            continue
        data_points.append(TimeSeriesDataPoint(date=date_str, count=row.count))
        total += row.count
    
    # Weekly aggregation
    if period == "weekly":
        weekly_data = {}
        for dp in data_points:
            date = datetime.strptime(dp.date, "%Y-%m-%d")
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            weekly_data[week_key] = weekly_data.get(week_key, 0) + dp.count
        
        data_points = [
            TimeSeriesDataPoint(date=k, count=v) 
            for k, v in sorted(weekly_data.items())
        ]
    
    # Monthly aggregation
    elif period == "monthly":
        monthly_data = {}
        for dp in data_points:
            month_key = dp.date[:7]  # YYYY-MM
            monthly_data[month_key] = monthly_data.get(month_key, 0) + dp.count
        
        data_points = [
            TimeSeriesDataPoint(date=f"{k}-01", count=v) 
            for k, v in sorted(monthly_data.items())
        ]
    
    return TimeSeriesMetrics(
        period=period,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        data_points=data_points,
        total=total
    )


async def get_meetings_over_time(
    db: AsyncSession,
    period: str = "daily",
    days: int = 30
) -> TimeSeriesMetrics:
    """Get meetings created over time."""
    # Add 1 day buffer to end_date to handle UTC vs local timezone differences
    end_date = datetime.now() + timedelta(days=1)
    start_date = datetime.now() - timedelta(days=days)
    
    query = select(
        func.date(MeetingRef.created_at).label("created_date"),
        func.count(MeetingRef.id).label("count")
    ).where(
        MeetingRef.created_at >= start_date,
        MeetingRef.created_at <= end_date
    ).group_by(
        func.date(MeetingRef.created_at)
    ).order_by(
        func.date(MeetingRef.created_at)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    data_points = []
    total = 0
    
    for row in rows:
        # Handle both date objects and strings (SQLite returns strings)
        if row.created_date:
            if hasattr(row.created_date, 'strftime'):
                date_str = row.created_date.strftime("%Y-%m-%d")
            else:
                date_str = str(row.created_date)[:10]
        else:
            continue
        data_points.append(TimeSeriesDataPoint(date=date_str, count=row.count))
        total += row.count
    
    # Weekly aggregation
    if period == "weekly":
        weekly_data = {}
        for dp in data_points:
            date = datetime.strptime(dp.date, "%Y-%m-%d")
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            weekly_data[week_key] = weekly_data.get(week_key, 0) + dp.count
        
        data_points = [
            TimeSeriesDataPoint(date=k, count=v) 
            for k, v in sorted(weekly_data.items())
        ]
    
    # Monthly aggregation
    elif period == "monthly":
        monthly_data = {}
        for dp in data_points:
            month_key = dp.date[:7]  # YYYY-MM
            monthly_data[month_key] = monthly_data.get(month_key, 0) + dp.count
        
        data_points = [
            TimeSeriesDataPoint(date=f"{k}-01", count=v) 
            for k, v in sorted(monthly_data.items())
        ]
    
    return TimeSeriesMetrics(
        period=period,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        data_points=data_points,
        total=total
    )


async def get_task_status_over_time(
    db: AsyncSession,
    period: str = "daily",
    days: int = 30
) -> TaskStatusOverTime:
    """Get task counts by status over time based on created_at date."""
    # Add 1 day buffer to end_date to handle UTC vs local timezone differences
    end_date = datetime.now() + timedelta(days=1)
    start_date = datetime.now() - timedelta(days=days)
    
    # Query tasks grouped by date and status
    query = select(
        func.date(Todo.created_at).label("created_date"),
        Todo.status,
        func.count(Todo.id).label("count")
    ).where(
        Todo.created_at >= start_date,
        Todo.created_at <= end_date
    ).group_by(
        func.date(Todo.created_at),
        Todo.status
    ).order_by(
        func.date(Todo.created_at)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Build a dict of date -> status -> count
    date_status_counts: dict[str, dict[str, int]] = {}
    totals = {"open": 0, "started": 0, "completed": 0, "cancelled": 0}
    
    for row in rows:
        # Handle both date objects and strings (SQLite returns strings)
        if row.created_date:
            if hasattr(row.created_date, 'strftime'):
                date_str = row.created_date.strftime("%Y-%m-%d")
            else:
                # SQLite returns date as string, extract YYYY-MM-DD
                date_str = str(row.created_date)[:10]
        else:
            continue
            
        if date_str not in date_status_counts:
            date_status_counts[date_str] = {"open": 0, "started": 0, "completed": 0, "cancelled": 0}
        
        # Map status to lowercase key
        status_key = row.status.lower() if row.status else "open"
        if status_key in date_status_counts[date_str]:
            date_status_counts[date_str][status_key] = row.count
            totals[status_key] = totals.get(status_key, 0) + row.count
    
    # Weekly aggregation
    if period == "weekly":
        weekly_data: dict[str, dict[str, int]] = {}
        for date_str, counts in date_status_counts.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.strftime("%Y-%m-%d")
            if week_key not in weekly_data:
                weekly_data[week_key] = {"open": 0, "started": 0, "completed": 0, "cancelled": 0}
            for status, count in counts.items():
                weekly_data[week_key][status] += count
        date_status_counts = weekly_data
    
    # Monthly aggregation
    elif period == "monthly":
        monthly_data: dict[str, dict[str, int]] = {}
        for date_str, counts in date_status_counts.items():
            month_key = f"{date_str[:7]}-01"
            if month_key not in monthly_data:
                monthly_data[month_key] = {"open": 0, "started": 0, "completed": 0, "cancelled": 0}
            for status, count in counts.items():
                monthly_data[month_key][status] += count
        date_status_counts = monthly_data
    
    # Convert to data points
    data_points = [
        StatusTimeSeriesDataPoint(
            date=date_str,
            open=counts.get("open", 0),
            started=counts.get("started", 0),
            completed=counts.get("completed", 0),
            cancelled=counts.get("cancelled", 0)
        )
        for date_str, counts in sorted(date_status_counts.items())
    ]
    
    return TaskStatusOverTime(
        period=period,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        data_points=data_points,
        totals=totals
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


@router.get("/organizations/created", response_model=TimeSeriesMetrics)
async def get_organizations_created_metrics(
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
    Get organization creation metrics over time.
    
    Returns the number of organizations created per day, week, or month
    within the specified time range.
    """
    if period not in ["daily", "weekly", "monthly"]:
        period = "daily"
    
    return await get_organizations_over_time(db, period, days)


@router.get("/meetings/created", response_model=TimeSeriesMetrics)
async def get_meetings_created_metrics(
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
    Get meeting creation metrics over time.
    
    Returns the number of meetings created per day, week, or month
    within the specified time range.
    """
    if period not in ["daily", "weekly", "monthly"]:
        period = "daily"
    
    return await get_meetings_over_time(db, period, days)


@router.get("/tasks/status-over-time", response_model=TaskStatusOverTime)
async def get_task_status_over_time_metrics(
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
    Get task status metrics over time.
    
    Returns the number of tasks created in each status (Open, Started, 
    Completed, Cancelled) per day, week, or month.
    """
    if period not in ["daily", "weekly", "monthly"]:
        period = "daily"
    
    return await get_task_status_over_time(db, period, days)


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
    
    Returns project metrics, task metrics, task completion over time,
    organizations created, and meetings created in a single response.
    """
    if period not in ["daily", "weekly", "monthly"]:
        period = "daily"
    
    projects = await get_project_metrics(db)
    tasks = await get_task_metrics(db)
    assets = await get_asset_metrics(db)
    tasks_completion = await get_tasks_completion_over_time(db, period, days)
    task_status_over_time = await get_task_status_over_time(db, period, days)
    organizations_created = await get_organizations_over_time(db, period, days)
    meetings_created = await get_meetings_over_time(db, period, days)
    
    return DashboardMetrics(
        projects=projects,
        tasks=tasks,
        assets=assets,
        tasks_completion=tasks_completion,
        task_status_over_time=task_status_over_time,
        organizations_created=organizations_created,
        meetings_created=meetings_created
    )

