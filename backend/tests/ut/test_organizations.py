import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_organization(client: AsyncClient):
    response = await client.post(
        "/api/organizations/",
        json={
            "name": "Acme Corporation",
            "stakeholders": "John Doe (CTO), Jane Smith (PM)",
            "team": "Alice, Bob",
            "description": "Enterprise organization focused on cloud migration",
            "related_products": "Platform API, Analytics Dashboard"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corporation"
    assert data["stakeholders"] == "John Doe (CTO), Jane Smith (PM)"
    assert data["team"] == "Alice, Bob"
    assert data["description"] == "Enterprise organization focused on cloud migration"
    assert data["related_products"] == "Platform API, Analytics Dashboard"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_organization_minimal(client: AsyncClient):
    response = await client.post(
        "/api/organizations/",
        json={"name": "Minimal Organization"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Organization"
    assert data["stakeholders"] is None
    assert data["team"] is None


@pytest.mark.asyncio
async def test_list_organizations(client: AsyncClient):
    # Create a few organizations
    for i in range(3):
        await client.post(
            "/api/organizations/",
            json={"name": f"Organization {i}"}
        )
    
    response = await client.get("/api/organizations/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["organizations"]) == 3


@pytest.mark.asyncio
async def test_list_organizations_pagination(client: AsyncClient):
    # Create 5 organizations
    for i in range(5):
        await client.post(
            "/api/organizations/",
            json={"name": f"Organization {i}"}
        )
    
    # Test pagination
    response = await client.get("/api/organizations/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["organizations"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2


@pytest.mark.asyncio
async def test_get_organization(client: AsyncClient):
    # Create an organization
    create_response = await client.post(
        "/api/organizations/",
        json={"name": "Test Organization"}
    )
    organization_id = create_response.json()["id"]
    
    # Get the organization
    response = await client.get(f"/api/organizations/{organization_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == organization_id
    assert data["name"] == "Test Organization"


@pytest.mark.asyncio
async def test_get_organization_not_found(client: AsyncClient):
    response = await client.get("/api/organizations/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_organization(client: AsyncClient):
    # Create an organization
    create_response = await client.post(
        "/api/organizations/",
        json={"name": "Original Name"}
    )
    organization_id = create_response.json()["id"]
    
    # Update the organization
    response = await client.put(
        f"/api/organizations/{organization_id}",
        json={
            "name": "Updated Name",
            "description": "New strategy notes"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "New strategy notes"


@pytest.mark.asyncio
async def test_update_organization_partial(client: AsyncClient):
    # Create an organization with all fields
    create_response = await client.post(
        "/api/organizations/",
        json={
            "name": "Full Organization",
            "stakeholders": "Original stakeholders",
            "description": "Original description"
        }
    )
    organization_id = create_response.json()["id"]
    
    # Update only description
    response = await client.put(
        f"/api/organizations/{organization_id}",
        json={"description": "Updated description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Full Organization"
    assert data["stakeholders"] == "Original stakeholders"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_organization_not_found(client: AsyncClient):
    response = await client.put(
        "/api/organizations/999",
        json={"name": "Updated Name"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_organization(client: AsyncClient):
    # Create an organization
    create_response = await client.post(
        "/api/organizations/",
        json={"name": "Delete Me"}
    )
    organization_id = create_response.json()["id"]
    
    # Delete the organization
    response = await client.delete(f"/api/organizations/{organization_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(f"/api/organizations/{organization_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_organization_not_found(client: AsyncClient):
    response = await client.delete("/api/organizations/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_organization_is_top_active(client: AsyncClient):
    # Create organization (default is_top_active false)
    create_response = await client.post(
        "/api/organizations/",
        json={"name": "Top Active Org"}
    )
    assert create_response.status_code == 201
    data = create_response.json()
    assert data.get("is_top_active") is False or data.get("is_top_active") == 0
    organization_id = data["id"]

    # Update to set is_top_active true
    update_response = await client.put(
        f"/api/organizations/{organization_id}",
        json={"is_top_active": True}
    )
    assert update_response.status_code == 200
    assert update_response.json().get("is_top_active") is True or update_response.json().get("is_top_active") == 1

    # List with top_active filter
    list_all = await client.get("/api/organizations/")
    assert list_all.status_code == 200
    list_active = await client.get("/api/organizations/?top_active=true")
    assert list_active.status_code == 200
    assert len(list_active.json()["organizations"]) >= 1
    assert any(o["id"] == organization_id for o in list_active.json()["organizations"])

    # Remove from top active
    await client.put(f"/api/organizations/{organization_id}", json={"is_top_active": False})
    list_active_after = await client.get("/api/organizations/?top_active=true")
    assert not any(o["id"] == organization_id for o in list_active_after.json()["organizations"])


@pytest.mark.asyncio
async def test_list_organization_todos_unions_direct_and_project_links(client: AsyncClient):
    org_r = await client.post(
        "/api/organizations/", json={"name": "Union Test Org"}
    )
    assert org_r.status_code == 201
    org_id = org_r.json()["id"]
    project_r = await client.post(
        "/api/projects/",
        json={"name": "Project In Org", "organization_id": org_id, "status": "Active"},
    )
    assert project_r.status_code == 201
    project_id = project_r.json()["id"]

    r1 = await client.post(
        "/api/todos/",
        json={"title": "Via project", "status": "Open", "project_id": project_id},
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/todos/",
        json={"title": "Direct org", "status": "Open", "organization_id": org_id},
    )
    assert r2.status_code == 201

    list_r = await client.get(f"/api/organizations/{org_id}/todos")
    assert list_r.status_code == 200
    data = list_r.json()
    assert data["total"] == 2
    titles = {t["title"] for t in data["todos"]}
    assert "Via project" in titles
    assert "Direct org" in titles

