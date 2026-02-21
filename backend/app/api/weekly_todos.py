import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.weekly_todo import (
    WeeklyTodoCreate,
    WeeklyTodoUpdate,
    WeeklyTodoResponse,
    WeeklyTodoListResponse,
    AllocationDayMinutes,
    AllocationResponse,
    AllocationListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weekly-todos", tags=["weekly-todos"])


@router.post("/", response_model=WeeklyTodoResponse, status_code=201)
async def create_weekly_todo(
    data: WeeklyTodoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new weekly todo."""
    logger.debug("POST /weekly-todos create title=%r todo_id=%s", data.title, data.todo_id)
    if data.todo_id is not None:
        todo = await crud.get_todo(db, data.todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
    return await crud.create_weekly_todo(db, data)


@router.get("/", response_model=WeeklyTodoListResponse)
async def list_weekly_todos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """List all weekly todos."""
    logger.debug("GET /weekly-todos list skip=%s limit=%s", skip, limit)
    items, total = await crud.get_weekly_todos(db, skip=skip, limit=limit)
    return WeeklyTodoListResponse(
        weekly_todos=items, total=total, skip=skip, limit=limit
    )


@router.get("/allocations", response_model=AllocationListResponse)
async def list_allocations_for_week(
    week_key: str = Query(..., description="ISO week key e.g. 2026-W08"),
    db: AsyncSession = Depends(get_db),
):
    """List all allocations for a given week."""
    logger.debug("GET /weekly-todos/allocations week_key=%s", week_key)
    allocations = await crud.list_allocations_for_week(db, week_key=week_key)
    return AllocationListResponse(allocations=allocations, week_key=week_key)


@router.get("/{weekly_todo_id}", response_model=WeeklyTodoResponse)
async def get_weekly_todo(
    weekly_todo_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a weekly todo by ID."""
    logger.debug("GET /weekly-todos/%s", weekly_todo_id)
    item = await crud.get_weekly_todo(db, weekly_todo_id)
    if not item:
        raise HTTPException(status_code=404, detail="Weekly todo not found")
    return item


@router.put("/{weekly_todo_id}", response_model=WeeklyTodoResponse)
async def update_weekly_todo(
    weekly_todo_id: int,
    data: WeeklyTodoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a weekly todo."""
    logger.debug("PUT /weekly-todos/%s", weekly_todo_id)
    if data.todo_id is not None:
        todo = await crud.get_todo(db, data.todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
    item = await crud.update_weekly_todo(db, weekly_todo_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Weekly todo not found")
    return item


@router.delete("/{weekly_todo_id}", status_code=204)
async def delete_weekly_todo(
    weekly_todo_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a weekly todo and its allocations."""
    logger.debug("DELETE /weekly-todos/%s", weekly_todo_id)
    success = await crud.delete_weekly_todo(db, weekly_todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Weekly todo not found")
    return None


@router.get("/{weekly_todo_id}/allocations/{week_key}", response_model=AllocationResponse)
async def get_allocation(
    weekly_todo_id: int,
    week_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Get allocation for a weekly todo and week."""
    item = await crud.get_weekly_todo(db, weekly_todo_id)
    if not item:
        raise HTTPException(status_code=404, detail="Weekly todo not found")
    allocation = await crud.get_allocation(db, weekly_todo_id, week_key)
    if not allocation:
        raise HTTPException(
            status_code=404,
            detail="Allocation not found for this week",
        )
    return allocation


@router.put("/{weekly_todo_id}/allocations/{week_key}", response_model=AllocationResponse)
async def put_allocation(
    weekly_todo_id: int,
    week_key: str,
    data: AllocationDayMinutes,
    db: AsyncSession = Depends(get_db),
):
    """Create or update allocation for a weekly todo and week."""
    logger.debug("PUT /weekly-todos/%s/allocations/%s", weekly_todo_id, week_key)
    item = await crud.get_weekly_todo(db, weekly_todo_id)
    if not item:
        raise HTTPException(status_code=404, detail="Weekly todo not found")
    return await crud.set_allocation(db, weekly_todo_id, week_key, data)
