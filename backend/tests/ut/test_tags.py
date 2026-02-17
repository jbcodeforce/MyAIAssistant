"""Unit tests for tags API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tags_empty(client: AsyncClient):
    """GET /api/tags/ returns empty list when no tags in DB."""
    response = await client.get("/api/tags/")
    assert response.status_code == 200
    data = response.json()
    assert "tags" in data
    assert data["tags"] == []


@pytest.mark.asyncio
async def test_list_tags_after_todo_with_tags(client: AsyncClient):
    """GET /api/tags/ returns distinct tags from todos."""
    r1 = await client.post(
        "/api/todos/",
        json={"title": "Todo A", "status": "Open", "tags": "planning,code"},
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/todos/",
        json={"title": "Todo B", "status": "Open", "tags": "planning,research"},
    )
    assert r2.status_code == 201
    # Verify todos have tags
    assert r1.json().get("tags") == "planning,code"
    assert r2.json().get("tags") == "planning,research"
    response = await client.get("/api/tags/")
    assert response.status_code == 200
    data = response.json()
    assert "tags" in data
    tags = data["tags"]
    assert isinstance(tags, list)
    # Distinct tags from both todos: planning, code, research (order may vary)
    assert len(tags) >= 2
    all_expected = {"planning", "code", "research"}
    assert all_expected.intersection(set(tags)) == all_expected
