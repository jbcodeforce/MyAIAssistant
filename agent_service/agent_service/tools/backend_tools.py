"""
Create task (todo) and create project tools.

When MYAI_BACKEND_URL is set, call the backend REST API.
When MYAI_USE_MOCK_TASKS is set (or backend URL is unset), return mock responses for tests.
"""

import os
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


def _backend_url() -> Optional[str]:
    url = os.environ.get("MYAI_BACKEND_URL", "").rstrip("/")
    return url or None


def _use_mock() -> bool:
    if os.environ.get("MYAI_USE_MOCK_TASKS", "").lower() in ("1", "true", "yes"):
        return True
    return _backend_url() is None


async def create_task(
    title: str,
    description: Optional[str] = None,
    status: str = "Open",
    urgency: Optional[str] = None,
    importance: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,
    project_id: Optional[int] = None,
) -> dict[str, Any]:
    """
    Create a todo/task in the MyAIAssistant backend.

    Use this when the user confirms they want to create a new task. Title is required.
    """
    if _use_mock():
        return {
            "id": 9001,
            "title": title,
            "description": description or "",
            "status": status,
            "message": f"Mock: created task '{title}' (use real backend with MYAI_BACKEND_URL for real create).",
        }
    url = f"{_backend_url()}/api/todos"
    payload = {"title": title, "status": status}
    if description is not None:
        payload["description"] = description
    if urgency is not None:
        payload["urgency"] = urgency
    if importance is not None:
        payload["importance"] = importance
    if category is not None:
        payload["category"] = category
    if tags is not None:
        payload["tags"] = tags
    if project_id is not None:
        payload["project_id"] = project_id
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {"id": data.get("id"), "title": data.get("title"), "message": "Task created."}


async def create_project(
    name: str,
    description: Optional[str] = None,
    status: str = "Draft",
    organization_id: Optional[int] = None,
    tasks: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a project in the MyAIAssistant backend.

    Use this when the user confirms they want to create a new project. Name is required.
    """
    if _use_mock():
        return {
            "id": 8001,
            "name": name,
            "description": description or "",
            "status": status,
            "message": f"Mock: created project '{name}' (use real backend with MYAI_BACKEND_URL for real create).",
        }
    url = f"{_backend_url()}/api/projects"
    payload = {"name": name, "status": status}
    if description is not None:
        payload["description"] = description
    if organization_id is not None:
        payload["organization_id"] = organization_id
    if tasks is not None:
        payload["tasks"] = tasks
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {"id": data.get("id"), "name": data.get("name"), "message": "Project created."}


# Registry for resolving tool names from agent config to callables
TASK_PROJECT_TOOL_REGISTRY: dict[str, Any] = {
    "create_task": create_task,
    "create_project": create_project,
}
