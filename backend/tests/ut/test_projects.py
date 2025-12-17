import pytest
from httpx import AsyncClient


@pytest.fixture
async def customer(client: AsyncClient) -> dict:
    """Create a customer for project tests."""
    response = await client.post(
        "/api/customers/",
        json={"name": "Test Customer"}
    )
    return response.json()


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient, customer: dict):
    response = await client.post(
        "/api/projects/",
        json={
            "name": "Q1 Platform Migration",
            "description": "Migrate customer to new platform version",
            "customer_id": customer["id"],
            "status": "Active",
            "tasks": "- Review requirements\n- Setup environment\n- Run migration"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Q1 Platform Migration"
    assert data["description"] == "Migrate customer to new platform version"
    assert data["customer_id"] == customer["id"]
    assert data["status"] == "Active"
    assert data["tasks"] == "- Review requirements\n- Setup environment\n- Run migration"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_project_minimal(client: AsyncClient):
    response = await client.post(
        "/api/projects/",
        json={"name": "Minimal Project"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Project"
    assert data["status"] == "Draft"
    assert data["customer_id"] is None


@pytest.mark.asyncio
async def test_create_project_invalid_customer(client: AsyncClient):
    response = await client.post(
        "/api/projects/",
        json={
            "name": "Project",
            "customer_id": 999
        }
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, customer: dict):
    # Create a few projects
    for i in range(3):
        await client.post(
            "/api/projects/",
            json={
                "name": f"Project {i}",
                "customer_id": customer["id"]
            }
        )
    
    response = await client.get("/api/projects/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["projects"]) == 3


@pytest.mark.asyncio
async def test_list_projects_filter_by_customer(client: AsyncClient):
    # Create two customers
    customer1 = (await client.post(
        "/api/customers/",
        json={"name": "Customer 1"}
    )).json()
    customer2 = (await client.post(
        "/api/customers/",
        json={"name": "Customer 2"}
    )).json()
    
    # Create projects for each customer
    await client.post(
        "/api/projects/",
        json={"name": "Project for C1", "customer_id": customer1["id"]}
    )
    await client.post(
        "/api/projects/",
        json={"name": "Project for C2", "customer_id": customer2["id"]}
    )
    
    # Filter by customer
    response = await client.get(f"/api/projects/?customer_id={customer1['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["projects"][0]["customer_id"] == customer1["id"]


@pytest.mark.asyncio
async def test_list_projects_filter_by_status(client: AsyncClient):
    # Create projects with different statuses
    await client.post(
        "/api/projects/",
        json={"name": "Active Project", "status": "Active"}
    )
    await client.post(
        "/api/projects/",
        json={"name": "Draft Project", "status": "Draft"}
    )
    
    response = await client.get("/api/projects/?status=Active")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["projects"][0]["status"] == "Active"


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    # Create a project
    create_response = await client.post(
        "/api/projects/",
        json={"name": "Test Project"}
    )
    project_id = create_response.json()["id"]
    
    # Get the project
    response = await client.get(f"/api/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Test Project"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    response = await client.get("/api/projects/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, customer: dict):
    # Create a project
    create_response = await client.post(
        "/api/projects/",
        json={"name": "Original Name", "status": "Draft"}
    )
    project_id = create_response.json()["id"]
    
    # Update the project
    response = await client.put(
        f"/api/projects/{project_id}",
        json={
            "name": "Updated Name",
            "status": "Active",
            "customer_id": customer["id"],
            "tasks": "- New task"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["status"] == "Active"
    assert data["customer_id"] == customer["id"]
    assert data["tasks"] == "- New task"


@pytest.mark.asyncio
async def test_update_project_invalid_customer(client: AsyncClient):
    # Create a project
    create_response = await client.post(
        "/api/projects/",
        json={"name": "Test Project"}
    )
    project_id = create_response.json()["id"]
    
    # Try to update with invalid customer
    response = await client.put(
        f"/api/projects/{project_id}",
        json={"customer_id": 999}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project_not_found(client: AsyncClient):
    response = await client.put(
        "/api/projects/999",
        json={"name": "Updated Name"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient):
    # Create a project
    create_response = await client.post(
        "/api/projects/",
        json={"name": "Delete Me"}
    )
    project_id = create_response.json()["id"]
    
    # Delete the project
    response = await client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(client: AsyncClient):
    response = await client.delete("/api/projects/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_project_todos(client: AsyncClient):
    # Create a project
    project_response = await client.post(
        "/api/projects/",
        json={"name": "Project with Todos"}
    )
    project_id = project_response.json()["id"]
    
    # Create todos linked to the project
    for i in range(3):
        await client.post(
            "/api/todos/",
            json={
                "title": f"Todo {i}",
                "status": "Open",
                "project_id": project_id
            }
        )
    
    # Create a todo not linked to the project
    await client.post(
        "/api/todos/",
        json={"title": "Unlinked Todo", "status": "Open"}
    )
    
    # Get todos for the project
    response = await client.get(f"/api/projects/{project_id}/todos")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["todos"]) == 3
    for todo in data["todos"]:
        assert todo["project_id"] == project_id


@pytest.mark.asyncio
async def test_list_project_todos_not_found(client: AsyncClient):
    response = await client.get("/api/projects/999/todos")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_project_status_lifecycle(client: AsyncClient):
    """Test project status transitions."""
    # Create a draft project
    create_response = await client.post(
        "/api/projects/",
        json={"name": "Lifecycle Project", "status": "Draft"}
    )
    project_id = create_response.json()["id"]
    assert create_response.json()["status"] == "Draft"
    
    # Activate
    response = await client.put(
        f"/api/projects/{project_id}",
        json={"status": "Active"}
    )
    assert response.json()["status"] == "Active"
    
    # Put on hold
    response = await client.put(
        f"/api/projects/{project_id}",
        json={"status": "On Hold"}
    )
    assert response.json()["status"] == "On Hold"
    
    # Complete
    response = await client.put(
        f"/api/projects/{project_id}",
        json={"status": "Completed"}
    )
    assert response.json()["status"] == "Completed"

