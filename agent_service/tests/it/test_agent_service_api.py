"""Integration tests for agent_service HTTP API (health, chat, rag, extract, tag)."""

import json
import os
import pytest
from httpx import AsyncClient



@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    """GET /health returns ready status and model."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ready"
    assert "model" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_chat_todo_contract(client: AsyncClient):
    """POST /chat/todo accepts valid body and returns message and context_used (or 503 if LLM down)."""
    response = await client.post(
        "/chat/todo",
        json={
            "message": "What is the first step?",
            "conversation_history": [],
            "use_rag": False,
            "task_title": "Test task",
            "task_description": "A test description",
        },
        timeout=60.0,
    )
    # 200 when LLM is available, 503 when not configured or unreachable
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "message" in data
        assert "context_used" in data
        assert isinstance(data["context_used"], list)


@pytest.mark.asyncio
async def test_chat_todo_validation(client: AsyncClient):
    """POST /chat/todo with empty message returns 422."""
    response = await client.post(
        "/chat/todo",
        json={
            "message": "",
            "conversation_history": [],
            "use_rag": False,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_generic_contract(client: AsyncClient):
    """POST /chat/generic accepts valid body and returns message (or 503)."""
    response = await client.post(
        "/chat/generic",
        json={
            "message": "Hello",
            "conversation_history": [],
            "context": {},
        },
        timeout=60.0,
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "message" in data
        assert "context_used" in data


@pytest.mark.asyncio
async def test_chat_generic_stream_contract(client: AsyncClient):
    """POST /chat/generic/stream returns NDJSON stream (or 503)."""
    response = await client.post(
        "/chat/generic/stream",
        json={
            "message": "Hi",
            "conversation_history": [],
        },
        timeout=60.0,
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        assert "application/x-ndjson" in response.headers.get("content-type", "")
        lines = [line for line in response.text.strip().split("\n") if line]
        assert len(lines) >= 1
        first = json.loads(lines[0])
        assert "content" in first or "done" in first


@pytest.mark.asyncio
async def test_rag_index_validation(client: AsyncClient):
    """POST /rag/index/{id} with empty content returns 400."""
    response = await client.post(
        "/rag/index/1",
        json={
            "title": "Doc",
            "uri": "file:///tmp/doc.md",
            "document_type": "markdown",
            "content": "",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_rag_index_contract(client: AsyncClient):
    """POST /rag/index/{id} with valid content returns success or 503 if knowledge unavailable."""
    response = await client.post(
        "/rag/index/1",
        json={
            "title": "Test doc",
            "uri": "file:///tmp/test.md",
            "document_type": "markdown",
            "content": "Some test content for indexing.",
        },
        timeout=120.0,
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert data.get("success") is True
        assert data.get("knowledge_id") == 1
        assert "chunks_indexed" in data


@pytest.mark.asyncio
async def test_rag_search_contract(client: AsyncClient):
    """POST /rag/search returns query and results (or 503)."""
    response = await client.post(
        "/rag/search",
        json={"query": "test query", "n_results": 3},
        timeout=30.0,
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert data.get("query") == "test query"
        assert "results" in data
        assert "total_results" in data


@pytest.mark.asyncio
async def test_rag_search_get_contract(client: AsyncClient):
    """GET /rag/search returns query and results (or 503)."""
    response = await client.get("/rag/search", params={"q": "hello", "n": 2})
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "query" in data
        assert "results" in data


@pytest.mark.asyncio
async def test_rag_stats_contract(client: AsyncClient):
    """GET /rag/stats returns collection stats (or 503)."""
    response = await client.get("/rag/stats")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "total_chunks" in data
        assert "collection_name" in data


@pytest.mark.asyncio
async def test_rag_remove_index_contract(client: AsyncClient):
    """DELETE /rag/index/{id} returns 200."""
    response = await client.delete("/rag/index/999")
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "message" in data


@pytest.mark.asyncio
async def test_extract_meeting_contract(client: AsyncClient):
    """POST /extract/meeting accepts content and returns structured fields (or 503)."""
    response = await client.post(
        "/extract/meeting",
        json={
            "content": "# Meeting Notes\n\n## Attendees\n- Alice\n- Bob\n\n## Key points\n- Discussed project timeline.\n\n## Next steps\n- Alice: Send summary by Friday.",
        },
        timeout=120.0,
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "attendees" in data
        assert "next_steps" in data
        assert "key_points" in data
        assert "cleaned_notes" in data
        assert isinstance(data["attendees"], list)
        assert isinstance(data["next_steps"], list)
        assert isinstance(data["key_points"], list)


@pytest.mark.asyncio
async def test_extract_meeting_validation(client: AsyncClient):
    """POST /extract/meeting with empty content returns 422."""
    response = await client.post("/extract/meeting", json={"content": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_tag_task_contract(client: AsyncClient):
    """POST /tag/task accepts title and description and returns message and tags (or 503)."""
    response = await client.post(
        "/tag/task",
        json={
            "task_title": "Fix login bug",
            "task_description": "Users cannot log in on mobile.",
        },
        timeout=60.0,
    )
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        data = response.json()
        assert "message" in data
        assert "tags" in data
        assert isinstance(data["tags"], list)


@pytest.mark.asyncio
async def test_tag_task_validation(client: AsyncClient):
    """POST /tag/task with empty title returns 422."""
    response = await client.post(
        "/tag/task",
        json={"task_title": "", "task_description": "Some description"},
    )
    assert response.status_code == 422
