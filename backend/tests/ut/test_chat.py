"""Unit tests for chat functionality."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_health(client: AsyncClient):
    """Test chat health check."""
    response = await client.get("/api/chat/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "provider" in data
    assert "model" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_chat_todo_not_found(client: AsyncClient):
    """Test chatting about a non-existent todo."""
    response = await client.post(
        "/api/chat/todo/9999",
        json={"message": "How should I approach this task?"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"


@pytest.mark.asyncio
async def test_chat_request_validation(client: AsyncClient):
    """Test chat request validation."""
    # Create a todo first
    create_response = await client.post(
        "/api/todos/",
        json={
            "title": "Test Todo",
            "status": "Open"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Test empty message
    response = await client.post(
        f"/api/chat/todo/{todo_id}",
        json={"message": ""}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_request_with_history(client: AsyncClient):
    """Test that conversation history is accepted in request."""
    # Create a todo
    create_response = await client.post(
        "/api/todos/",
        json={
            "title": "Complex Task",
            "description": "A multi-step project",
            "status": "Open"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Make request with conversation history
    # This will fail due to missing API key, but validates the schema
    response = await client.post(
        f"/api/chat/todo/{todo_id}",
        json={
            "message": "What about the second step?",
            "conversation_history": [
                {"role": "user", "content": "How do I start?"},
                {"role": "assistant", "content": "First, you should..."}
            ],
            "use_rag": False
        }
    )
    
    # Should not be a validation error
    assert response.status_code != 422


@pytest.mark.asyncio
async def test_chat_invalid_history_role(client: AsyncClient):
    """Test that invalid roles in history are rejected."""
    # Create a todo
    create_response = await client.post(
        "/api/todos/",
        json={
            "title": "Test Task",
            "status": "Open"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Make request with invalid role
    response = await client.post(
        f"/api/chat/todo/{todo_id}",
        json={
            "message": "Hello",
            "conversation_history": [
                {"role": "invalid_role", "content": "Test"}
            ]
        }
    )
    
    # Should be a validation error
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_generic_chat_api(client: AsyncClient):
    """Test /api/chat endpoint (generic model chat endpoint) with minimal payload."""
    response = await client.post(
        "/api/chat/generic",
        json={"message": "Hello, who are you?"}
    )
    # Should not get a validation error
    assert response.status_code != 422
    # If missing API key, may get 401/403 or 500; just verify not 422
    # Optionally check response is JSON
    assert response.headers["content-type"].startswith("application/json")
    # Optionally, ensure schema of response (error or not) has "detail" or "result/message" fields
    data = response.json()
    assert isinstance(data, dict)
