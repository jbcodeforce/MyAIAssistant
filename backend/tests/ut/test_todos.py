import pytest
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

