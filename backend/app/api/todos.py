from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
from app.schemas.task_plan import TaskPlanCreate, TaskPlanUpdate, TaskPlanResponse


router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("/", response_model=TodoResponse, status_code=201)
async def create_todo(
    todo: TodoCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new todo item.
    """
    return await crud.create_todo(db=db, todo=todo)


@router.get("/", response_model=TodoListResponse)
async def list_todos(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    urgency: Optional[str] = Query(None, description="Filter by urgency"),
    importance: Optional[str] = Query(None, description="Filter by importance"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of todos with optional filtering.
    """
    todos, total = await crud.get_todos(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        urgency=urgency,
        importance=importance,
        category=category
    )
    return TodoListResponse(todos=todos, total=total, skip=skip, limit=limit)


@router.get("/unclassified", response_model=TodoListResponse)
async def list_unclassified_todos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve todos that have not been classified with urgency/importance.
    """
    todos, total = await crud.get_unclassified_todos(db=db, skip=skip, limit=limit)
    return TodoListResponse(todos=todos, total=total, skip=skip, limit=limit)


@router.get("/canvas/{urgency}/{importance}", response_model=TodoListResponse)
async def list_todos_by_quadrant(
    urgency: str,
    importance: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve todos for a specific urgency/importance quadrant (for canvas view).
    """
    todos, total = await crud.get_todos_by_urgency_importance(
        db=db,
        urgency=urgency,
        importance=importance,
        skip=skip,
        limit=limit
    )
    return TodoListResponse(todos=todos, total=total, skip=skip, limit=limit)


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a specific todo by ID.
    """
    todo = await crud.get_todo(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a todo item.
    """
    todo = await crud.update_todo(db=db, todo_id=todo_id, todo_update=todo_update)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a todo item.
    """
    success = await crud.delete_todo(db=db, todo_id=todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return None


# Task Plan endpoints

@router.get("/{todo_id}/plan", response_model=TaskPlanResponse)
async def get_task_plan(
    todo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the task plan for a specific todo.
    """
    # First verify the todo exists
    todo = await crud.get_todo(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    task_plan = await crud.get_task_plan_by_todo_id(db=db, todo_id=todo_id)
    if not task_plan:
        raise HTTPException(status_code=404, detail="Task plan not found")
    return task_plan


@router.put("/{todo_id}/plan", response_model=TaskPlanResponse)
async def save_task_plan(
    todo_id: int,
    task_plan: TaskPlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create or update the task plan for a specific todo.
    """
    # First verify the todo exists
    todo = await crud.get_todo(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    result = await crud.upsert_task_plan(db=db, todo_id=todo_id, content=task_plan.content)
    return result


@router.delete("/{todo_id}/plan", status_code=204)
async def delete_task_plan(
    todo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete the task plan for a specific todo.
    """
    # First verify the todo exists
    todo = await crud.get_todo(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    success = await crud.delete_task_plan(db=db, todo_id=todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task plan not found")
    return None

