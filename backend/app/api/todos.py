from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db import crud
from app.api.schemas.todo import TodoCreate, TodoUpdate, TodoResponse, TodoListResponse
from app.api.schemas.task_plan import TaskPlanCreate, TaskPlanUpdate, TaskPlanResponse
from app.core.config import get_settings, resolve_agent_config_dir
from app.tagging.service import BackendTaskTaggingToolProvider
from agent_core.agents.agent_factory import get_agent_factory
from agent_core.agents.base_agent import AgentInput


router = APIRouter(prefix="/todos", tags=["todos"])


class TagTaskResponse(BaseModel):
    """Response from POST /todos/{todo_id}/tag."""

    message: str = Field(..., description="Agent reply")
    tags: list[str] = Field(default_factory=list, description="Tags assigned")
    agent_type: str = Field(default="task_tagging", description="Agent that performed tagging")


@router.post("/", response_model=TodoResponse, status_code=201)
async def create_todo(
    todo: TodoCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new todo item.
    """
    return await crud.create_todo(db=db, todo=todo)


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO date or datetime string to datetime; return None if invalid or empty."""
    if not value or not value.strip():
        return None
    value = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@router.get("/", response_model=TodoListResponse)
async def list_todos(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    urgency: Optional[str] = Query(None, description="Filter by urgency"),
    importance: Optional[str] = Query(None, description="Filter by importance"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(
        None, max_length=200, description="Filter by substring in title or description"
    ),
    completed_after: Optional[str] = Query(None, description="Filter by completed_at >= (ISO date/datetime)"),
    completed_before: Optional[str] = Query(None, description="Filter by completed_at <= (ISO date/datetime)"),
    updated_after: Optional[str] = Query(None, description="Filter by updated_at >= (ISO date/datetime)"),
    updated_before: Optional[str] = Query(None, description="Filter by updated_at <= (ISO date/datetime)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a list of todos with optional filtering.
    """
    completed_after_dt = _parse_iso_datetime(completed_after)
    completed_before_dt = _parse_iso_datetime(completed_before)
    updated_after_dt = _parse_iso_datetime(updated_after)
    updated_before_dt = _parse_iso_datetime(updated_before)
    todos, total = await crud.get_todos(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        urgency=urgency,
        importance=importance,
        category=category,
        search=search,
        completed_after=completed_after_dt,
        completed_before=completed_before_dt,
        updated_after=updated_after_dt,
        updated_before=updated_before_dt,
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


@router.post("/{todo_id}/tag", response_model=TagTaskResponse)
async def tag_task(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Run the task-tagging agent on this todo. Uses Claude Agent SDK and backend
    tools (get_available_tags, task_list, update_task) to classify and persist tags.
    Requires ANTHROPIC_API_KEY when using TaskTaggingAgent.
    """
    todo = await crud.get_todo(db=db, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    settings = get_settings()
    config_dir = resolve_agent_config_dir(settings.agent_config_dir)
    factory = get_agent_factory(config_dir=config_dir)
    provider = BackendTaskTaggingToolProvider(db=db)
    agent = factory.create_agent("TaskTaggingAgent", tool_provider=provider)
    query_text = "Tag this task based on its title and description. Use get_available_tags first, then update_task with the chosen tags."
    context = {
        "todo_id": todo_id,
        "task_title": todo.title,
        "task_description": todo.description or "",
    }
    response = await agent.execute(AgentInput(query=query_text, context=context))
    tags = response.metadata.get("tags") or []
    return TagTaskResponse(
        message=response.message,
        tags=tags,
        agent_type=response.agent_type or "task_tagging",
    )


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

