"""Unit tests for chat functionality."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_config(client: AsyncClient):
    """Test getting chat configuration."""
    response = await client.get("/api/chat/config")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "model" in data
    assert "max_tokens" in data
    assert "temperature" in data
    assert "rag_enabled" in data


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
async def test_chat_todo_no_api_key(client: AsyncClient):
    """Test chatting without API key configured (for non-Ollama providers)."""
    # Create a todo first
    create_response = await client.post(
        "/api/todos/",
        json={
            "title": "Test Todo for Chat",
            "description": "This is a test task",
            "status": "Open"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Try to chat - this should fail if no API key is set
    # The behavior depends on the provider configured
    response = await client.post(
        f"/api/chat/todo/{todo_id}",
        json={
            "message": "How should I approach this task?",
            "use_rag": False  # Disable RAG for simpler test
        }
    )
    
    # For default OpenAI provider without key, this should return an error
    # For Ollama, it would try to connect to local server
    # We accept either 400 (missing API key) or 500 (connection error)
    assert response.status_code in [400, 500]


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

