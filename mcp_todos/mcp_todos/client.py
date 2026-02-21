"""HTTP client for MyAIAssistant backend todos API."""

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


def get_base_url() -> str:
    return os.environ.get("MYAI_BACKEND_URL", DEFAULT_BASE_URL)


async def create_todo(client: httpx.AsyncClient, payload: dict[str, Any]) -> tuple[int, str]:
    """POST /api/todos/. Returns (status_code, response_text)."""
    r = await client.post("/api/todos/", json=payload)
    return r.status_code, r.text


async def search_todos(
    client: httpx.AsyncClient,
    search: str | None = None,
    status: str | None = None,
    category: str | None = None,
    limit: int = 100,
    skip: int = 0,
) -> tuple[int, str]:
    """GET /api/todos/ with query params. Returns (status_code, response_text)."""
    params: dict[str, str | int] = {"limit": limit, "skip": skip}
    if search:
        params["search"] = search
    if status:
        params["status"] = status
    if category:
        params["category"] = category
    r = await client.get("/api/todos/", params=params)
    return r.status_code, r.text


async def get_todo(client: httpx.AsyncClient, todo_id: int) -> tuple[int, str]:
    """GET /api/todos/{id}. Returns (status_code, response_text)."""
    r = await client.get(f"/api/todos/{todo_id}")
    return r.status_code, r.text


async def update_todo(
    client: httpx.AsyncClient, todo_id: int, payload: dict[str, Any]
) -> tuple[int, str]:
    """PUT /api/todos/{id}. Returns (status_code, response_text)."""
    r = await client.put(f"/api/todos/{todo_id}", json=payload)
    return r.status_code, r.text


async def delete_todo(client: httpx.AsyncClient, todo_id: int) -> tuple[int, str]:
    """DELETE /api/todos/{id}. Returns (status_code, response_text)."""
    r = await client.delete(f"/api/todos/{todo_id}")
    return r.status_code, r.text
