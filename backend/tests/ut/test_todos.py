import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_todo(client: AsyncClient):
    response = await client.post(
        "/api/todos/",
        json={
            "title": "Test Todo",
            "description": "This is a test todo",
            "status": "Open",
            "urgency": "Urgent",
            "importance": "Important",
            "category": "Testing"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "This is a test todo"
    assert data["status"] == "Open"
    assert data["urgency"] == "Urgent"
    assert data["importance"] == "Important"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_todo_with_tags(client: AsyncClient):
    response = await client.post(
        "/api/todos/",
        json={
            "title": "Tagged Todo",
            "status": "Open",
            "tags": "planning,code"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tags"] == "planning,code"


@pytest.mark.asyncio
async def test_update_todo_tags(client: AsyncClient):
    create_response = await client.post(
        "/api/todos/",
        json={"title": "Todo to tag", "status": "Open"}
    )
    todo_id = create_response.json()["id"]
    response = await client.put(
        f"/api/todos/{todo_id}",
        json={"tags": "research,documentation"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == "research,documentation"


@pytest.mark.asyncio
async def test_list_todos(client: AsyncClient):
    # Create a few todos
    for i in range(3):
        await client.post(
            "/api/todos/",
            json={
                "title": f"Test Todo {i}",
                "status": "Open"
            }
        )
    
    response = await client.get("/api/todos/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["todos"]) == 3


@pytest.mark.asyncio
async def test_get_todo(client: AsyncClient):
    # Create a todo
    create_response = await client.post(
        "/api/todos/",
        json={
            "title": "Test Todo",
            "status": "Open"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Get the todo
    response = await client.get(f"/api/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Test Todo"


@pytest.mark.asyncio
async def test_get_todo_not_found(client: AsyncClient):
    response = await client.get("/api/todos/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_todo(client: AsyncClient):
    # Create a todo
    create_response = await client.post(
        "/api/todos/",
        json={
            "title": "Test Todo",
            "status": "Open"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Update the todo
    response = await client.put(
        f"/api/todos/{todo_id}",
        json={
            "status": "Started",
            "urgency": "Urgent"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Started"
    assert data["urgency"] == "Urgent"


@pytest.mark.asyncio
async def test_update_todo_to_completed(client: AsyncClient):
    # Create a todo
    create_response = await client.post(
        "/api/todos/",
        json={
            "title": "Test Todo",
            "status": "Open"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Update to completed
    response = await client.put(
        f"/api/todos/{todo_id}",
        json={"status": "Completed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Completed"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_delete_todo(client: AsyncClient):
    # Create a todo
    create_response = await client.post(
        "/api/todos/",
        json={
            "title": "Test Todo",
            "status": "Open"
        }
    )
    todo_id = create_response.json()["id"]
    
    # Delete the todo
    response = await client.delete(f"/api/todos/{todo_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(f"/api/todos/{todo_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_todos_with_date_filters(client: AsyncClient):
    """List todos with completed_after filter."""
    create_response = await client.post(
        "/api/todos/",
        json={"title": "To Complete", "status": "Open"},
    )
    assert create_response.status_code == 201
    todo_id = create_response.json()["id"]
    await client.put(f"/api/todos/{todo_id}", json={"status": "Completed"})
    # List with completed_after in the past: should include this todo
    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    response = await client.get(f"/api/todos/?completed_after={past}&status=Completed")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(t["id"] == todo_id for t in data["todos"])


@pytest.mark.asyncio
async def test_list_todos_with_filters(client: AsyncClient):
    # Create todos with different attributes
    await client.post(
        "/api/todos/",
        json={
            "title": "Urgent Important Todo",
            "status": "Open",
            "urgency": "Urgent",
            "importance": "Important"
        }
    )
    await client.post(
        "/api/todos/",
        json={
            "title": "Not Urgent Todo",
            "status": "Open",
            "urgency": "Not Urgent",
            "importance": "Important"
        }
    )
    
    # Filter by urgency
    response = await client.get("/api/todos/?urgency=Urgent")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["todos"][0]["urgency"] == "Urgent"


@pytest.mark.asyncio
async def test_list_unclassified_todos(client: AsyncClient):
    # Create classified todo
    await client.post(
        "/api/todos/",
        json={
            "title": "Classified Todo",
            "status": "Open",
            "urgency": "Urgent",
            "importance": "Important"
        }
    )
    
    # Create unclassified todo
    await client.post(
        "/api/todos/",
        json={
            "title": "Unclassified Todo",
            "status": "Open"
        }
    )
    
    response = await client.get("/api/todos/unclassified")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["todos"][0]["title"] == "Unclassified Todo"


@pytest.mark.asyncio
async def test_list_todos_by_quadrant(client: AsyncClient):
    # Create todos in different quadrants
    await client.post(
        "/api/todos/",
        json={
            "title": "Urgent Important Todo",
            "status": "Open",
            "urgency": "Urgent",
            "importance": "Important"
        }
    )
    await client.post(
        "/api/todos/",
        json={
            "title": "Not Urgent Important Todo",
            "status": "Open",
            "urgency": "Not Urgent",
            "importance": "Important"
        }
    )
    
    response = await client.get("/api/todos/canvas/Urgent/Important")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["todos"][0]["urgency"] == "Urgent"
    assert data["todos"][0]["importance"] == "Important"


@pytest.mark.asyncio
async def test_list_todos_with_search(client: AsyncClient):
    await client.post(
        "/api/todos/",
        json={
            "title": "Review project documentation",
            "description": "Check the README and API docs",
            "status": "Open",
        },
    )
    await client.post(
        "/api/todos/",
        json={
            "title": "Deploy to staging",
            "description": "Run the deployment script for staging",
            "status": "Open",
        },
    )
    await client.post(
        "/api/todos/",
        json={
            "title": "Weekly sync",
            "description": "Team standup and backlog review",
            "status": "Started",
        },
    )

    response = await client.get("/api/todos/?search=documentation")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "documentation" in data["todos"][0]["title"].lower()

    response = await client.get("/api/todos/?search=staging")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "staging" in data["todos"][0]["description"].lower()

    response = await client.get("/api/todos/?search=nonexistentword")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["todos"]) == 0

    response = await client.get("/api/todos/?search=")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_tag_task_not_found(client: AsyncClient):
    response = await client.post("/api/todos/999/tag")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tag_task_mock_agent(client: AsyncClient):
    """POST /api/todos/{id}/tag returns tags from agent (mocked to avoid Claude call)."""
    create_response = await client.post(
        "/api/todos/",
        json={"title": "Task to tag", "description": "Review docs", "status": "Open"},
    )
    todo_id = create_response.json()["id"]

    mock_response = type("R", (), {})()
    mock_response.message = "Tagged with planning, documentation."
    mock_response.metadata = {"tags": ["planning", "documentation"]}
    mock_response.agent_type = "task_tagging"

    mock_agent = AsyncMock()
    mock_agent.execute = AsyncMock(return_value=mock_response)

    mock_factory = type("F", (), {})()
    mock_factory.create_agent = lambda name, **kw: mock_agent

    with patch("app.api.todos.get_agent_factory", return_value=mock_factory):
        response = await client.post(f"/api/todos/{todo_id}/tag")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "task_tagging"
    assert "planning" in data["tags"]
    assert "documentation" in data["tags"]
    assert "Tagged" in data["message"]


@pytest.mark.asyncio
async def test_metrics_tasks_completed_by_month(client: AsyncClient):
    """GET /api/metrics/tasks/completed-by-month returns list of {period, count}."""
    response = await client.get("/api/metrics/tasks/completed-by-month?since_days=365")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "period" in item
        assert "count" in item
        assert isinstance(item["period"], str)
        assert isinstance(item["count"], int)

