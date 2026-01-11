import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_person(client: AsyncClient):
    response = await client.post(
        "/api/persons/",
        json={
            "name": "John Doe",
            "context": "Technical lead on the migration project",
            "role": "Engineering Manager",
            "next_step": "Schedule follow-up meeting to discuss timeline"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["context"] == "Technical lead on the migration project"
    assert data["role"] == "Engineering Manager"
    assert data["next_step"] == "Schedule follow-up meeting to discuss timeline"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_person_minimal(client: AsyncClient):
    response = await client.post(
        "/api/persons/",
        json={"name": "Jane Smith"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Smith"
    assert data["context"] is None
    assert data["role"] is None
    assert data["next_step"] is None
    assert data["last_met_date"] is None


@pytest.mark.asyncio
async def test_create_person_with_last_met_date(client: AsyncClient):
    response = await client.post(
        "/api/persons/",
        json={
            "name": "Alice Johnson",
            "role": "Product Manager",
            "last_met_date": "2026-01-05T14:00:00"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice Johnson"
    assert data["role"] == "Product Manager"
    assert data["last_met_date"] is not None


@pytest.mark.asyncio
async def test_create_person_with_project(client: AsyncClient):
    # First create a project
    project_response = await client.post(
        "/api/projects/",
        json={"name": "Test Project"}
    )
    project_id = project_response.json()["id"]
    
    # Create person linked to project
    response = await client.post(
        "/api/persons/",
        json={
            "name": "Bob Williams",
            "role": "Developer",
            "project_id": project_id
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bob Williams"
    assert data["project_id"] == project_id


@pytest.mark.asyncio
async def test_create_person_with_organization(client: AsyncClient):
    # First create an organization
    org_response = await client.post(
        "/api/organizations/",
        json={"name": "Acme Corp"}
    )
    org_id = org_response.json()["id"]
    
    # Create person linked to organization
    response = await client.post(
        "/api/persons/",
        json={
            "name": "Carol Davis",
            "role": "CTO",
            "organization_id": org_id
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Carol Davis"
    assert data["organization_id"] == org_id


@pytest.mark.asyncio
async def test_create_person_invalid_project(client: AsyncClient):
    response = await client.post(
        "/api/persons/",
        json={
            "name": "Invalid Project Person",
            "project_id": 9999
        }
    )
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_person_invalid_organization(client: AsyncClient):
    response = await client.post(
        "/api/persons/",
        json={
            "name": "Invalid Org Person",
            "organization_id": 9999
        }
    )
    assert response.status_code == 404
    assert "Organization not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_persons(client: AsyncClient):
    # Create a few persons
    for i in range(3):
        await client.post(
            "/api/persons/",
            json={"name": f"Person {i}"}
        )
    
    response = await client.get("/api/persons/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["persons"]) == 3


@pytest.mark.asyncio
async def test_list_persons_pagination(client: AsyncClient):
    # Create 5 persons
    for i in range(5):
        await client.post(
            "/api/persons/",
            json={"name": f"Person {i}"}
        )
    
    # Test pagination
    response = await client.get("/api/persons/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["persons"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2


@pytest.mark.asyncio
async def test_list_persons_filter_by_project(client: AsyncClient):
    # Create a project
    project_response = await client.post(
        "/api/projects/",
        json={"name": "Filter Project"}
    )
    project_id = project_response.json()["id"]
    
    # Create persons - 2 linked to project, 1 not
    await client.post("/api/persons/", json={"name": "Person 1", "project_id": project_id})
    await client.post("/api/persons/", json={"name": "Person 2", "project_id": project_id})
    await client.post("/api/persons/", json={"name": "Person 3"})
    
    # Filter by project
    response = await client.get(f"/api/persons/?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["persons"]) == 2


@pytest.mark.asyncio
async def test_list_persons_filter_by_organization(client: AsyncClient):
    # Create an organization
    org_response = await client.post(
        "/api/organizations/",
        json={"name": "Filter Organization"}
    )
    org_id = org_response.json()["id"]
    
    # Create persons - 2 linked to org, 1 not
    await client.post("/api/persons/", json={"name": "Person 1", "organization_id": org_id})
    await client.post("/api/persons/", json={"name": "Person 2", "organization_id": org_id})
    await client.post("/api/persons/", json={"name": "Person 3"})
    
    # Filter by organization
    response = await client.get(f"/api/persons/?organization_id={org_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["persons"]) == 2


@pytest.mark.asyncio
async def test_get_person(client: AsyncClient):
    # Create a person
    create_response = await client.post(
        "/api/persons/",
        json={"name": "Test Person", "role": "Tester"}
    )
    person_id = create_response.json()["id"]
    
    # Get the person
    response = await client.get(f"/api/persons/{person_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == person_id
    assert data["name"] == "Test Person"
    assert data["role"] == "Tester"


@pytest.mark.asyncio
async def test_get_person_not_found(client: AsyncClient):
    response = await client.get("/api/persons/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_person(client: AsyncClient):
    # Create a person
    create_response = await client.post(
        "/api/persons/",
        json={"name": "Original Name"}
    )
    person_id = create_response.json()["id"]
    
    # Update the person
    response = await client.put(
        f"/api/persons/{person_id}",
        json={
            "name": "Updated Name",
            "role": "New Role",
            "context": "New context information"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["role"] == "New Role"
    assert data["context"] == "New context information"


@pytest.mark.asyncio
async def test_update_person_partial(client: AsyncClient):
    # Create a person with all fields
    create_response = await client.post(
        "/api/persons/",
        json={
            "name": "Full Person",
            "role": "Original role",
            "context": "Original context",
            "next_step": "Original next step"
        }
    )
    person_id = create_response.json()["id"]
    
    # Update only context
    response = await client.put(
        f"/api/persons/{person_id}",
        json={"context": "Updated context"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Full Person"
    assert data["role"] == "Original role"
    assert data["context"] == "Updated context"
    assert data["next_step"] == "Original next step"


@pytest.mark.asyncio
async def test_update_person_not_found(client: AsyncClient):
    response = await client.put(
        "/api/persons/999",
        json={"name": "Updated Name"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_person_with_project(client: AsyncClient):
    # Create a project
    project_response = await client.post(
        "/api/projects/",
        json={"name": "New Project"}
    )
    project_id = project_response.json()["id"]
    
    # Create a person
    create_response = await client.post(
        "/api/persons/",
        json={"name": "Person to Link"}
    )
    person_id = create_response.json()["id"]
    
    # Update to link project
    response = await client.put(
        f"/api/persons/{person_id}",
        json={"project_id": project_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_id


@pytest.mark.asyncio
async def test_update_person_invalid_project(client: AsyncClient):
    # Create a person
    create_response = await client.post(
        "/api/persons/",
        json={"name": "Person"}
    )
    person_id = create_response.json()["id"]
    
    # Try to update with invalid project
    response = await client.put(
        f"/api/persons/{person_id}",
        json={"project_id": 9999}
    )
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_person_invalid_organization(client: AsyncClient):
    # Create a person
    create_response = await client.post(
        "/api/persons/",
        json={"name": "Person"}
    )
    person_id = create_response.json()["id"]
    
    # Try to update with invalid organization
    response = await client.put(
        f"/api/persons/{person_id}",
        json={"organization_id": 9999}
    )
    assert response.status_code == 404
    assert "Organization not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_person(client: AsyncClient):
    # Create a person
    create_response = await client.post(
        "/api/persons/",
        json={"name": "Delete Me"}
    )
    person_id = create_response.json()["id"]
    
    # Delete the person
    response = await client.delete(f"/api/persons/{person_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(f"/api/persons/{person_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_person_not_found(client: AsyncClient):
    response = await client.delete("/api/persons/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_person_validation_missing_name(client: AsyncClient):
    response = await client.post(
        "/api/persons/",
        json={"role": "Some Role"}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_persons_empty(client: AsyncClient):
    response = await client.get("/api/persons/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["persons"]) == 0


@pytest.mark.asyncio
async def test_person_timestamps(client: AsyncClient):
    # Create a person
    create_response = await client.post(
        "/api/persons/",
        json={"name": "Timestamp Test"}
    )
    assert create_response.status_code == 201
    data = create_response.json()
    
    # Check timestamps exist and are valid
    assert "created_at" in data
    assert "updated_at" in data
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


@pytest.mark.asyncio
async def test_update_person_with_last_met_date(client: AsyncClient):
    # Create a person
    create_response = await client.post(
        "/api/persons/",
        json={"name": "Meeting Person"}
    )
    person_id = create_response.json()["id"]
    
    # Update with last_met_date
    response = await client.put(
        f"/api/persons/{person_id}",
        json={"last_met_date": "2026-01-10T10:30:00"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["last_met_date"] is not None


@pytest.mark.asyncio
async def test_create_person_with_full_data(client: AsyncClient):
    # Create project and organization first
    project_response = await client.post(
        "/api/projects/",
        json={"name": "Full Test Project"}
    )
    project_id = project_response.json()["id"]
    
    org_response = await client.post(
        "/api/organizations/",
        json={"name": "Full Test Organization"}
    )
    org_id = org_response.json()["id"]
    
    # Create person with all fields
    response = await client.post(
        "/api/persons/",
        json={
            "name": "Complete Person",
            "context": "## Background\n\nTechnical lead for the platform team.",
            "role": "Senior Engineering Manager",
            "last_met_date": "2026-01-08T15:00:00",
            "next_step": "- Send proposal\n- Schedule demo",
            "project_id": project_id,
            "organization_id": org_id
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Complete Person"
    assert data["context"] == "## Background\n\nTechnical lead for the platform team."
    assert data["role"] == "Senior Engineering Manager"
    assert data["next_step"] == "- Send proposal\n- Schedule demo"
    assert data["project_id"] == project_id
    assert data["organization_id"] == org_id
    assert data["last_met_date"] is not None
