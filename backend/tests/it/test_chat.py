"""Unit tests for chat API (agent-service only)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_health(client: AsyncClient):
    response = await client.get("/api/chat/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "agent_service"
    assert data.get("agent_service_url")
    assert "message" in data


@pytest.mark.asyncio
async def test_chat_todo_returns_503(client: AsyncClient):
    response = await client.post(
        "/api/chat/todo/9999",
        json={"message": "How should I approach this task?"},
    )
    assert response.status_code == 503
    assert "agent_service" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generic_chat_returns_503(client: AsyncClient):
    response = await client.post(
        "/api/chat/generic",
        json={"message": "Hello, who are you?"},
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_generic_chat_stream_returns_503(client: AsyncClient):
    response = await client.post(
        "/api/chat/generic/stream",
        json={"message": "Hi"},
    )
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_kb_chat_returns_503(client: AsyncClient):
    response = await client.post(
        "/api/chat/kb",
        json={"message": "Search the knowledge base"},
    )
    assert response.status_code == 503
