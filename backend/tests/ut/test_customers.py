import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_customer(client: AsyncClient):
    response = await client.post(
        "/api/customers/",
        json={
            "name": "Acme Corporation",
            "stakeholders": "John Doe (CTO), Jane Smith (PM)",
            "team": "Alice, Bob",
            "description": "Enterprise customer focused on cloud migration",
            "related_products": "Platform API, Analytics Dashboard"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corporation"
    assert data["stakeholders"] == "John Doe (CTO), Jane Smith (PM)"
    assert data["team"] == "Alice, Bob"
    assert data["description"] == "Enterprise customer focused on cloud migration"
    assert data["related_products"] == "Platform API, Analytics Dashboard"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_customer_minimal(client: AsyncClient):
    response = await client.post(
        "/api/customers/",
        json={"name": "Minimal Customer"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Minimal Customer"
    assert data["stakeholders"] is None
    assert data["team"] is None


@pytest.mark.asyncio
async def test_list_customers(client: AsyncClient):
    # Create a few customers
    for i in range(3):
        await client.post(
            "/api/customers/",
            json={"name": f"Customer {i}"}
        )
    
    response = await client.get("/api/customers/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["customers"]) == 3


@pytest.mark.asyncio
async def test_list_customers_pagination(client: AsyncClient):
    # Create 5 customers
    for i in range(5):
        await client.post(
            "/api/customers/",
            json={"name": f"Customer {i}"}
        )
    
    # Test pagination
    response = await client.get("/api/customers/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["customers"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2


@pytest.mark.asyncio
async def test_get_customer(client: AsyncClient):
    # Create a customer
    create_response = await client.post(
        "/api/customers/",
        json={"name": "Test Customer"}
    )
    customer_id = create_response.json()["id"]
    
    # Get the customer
    response = await client.get(f"/api/customers/{customer_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == customer_id
    assert data["name"] == "Test Customer"


@pytest.mark.asyncio
async def test_get_customer_not_found(client: AsyncClient):
    response = await client.get("/api/customers/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_customer(client: AsyncClient):
    # Create a customer
    create_response = await client.post(
        "/api/customers/",
        json={"name": "Original Name"}
    )
    customer_id = create_response.json()["id"]
    
    # Update the customer
    response = await client.put(
        f"/api/customers/{customer_id}",
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
async def test_update_customer_partial(client: AsyncClient):
    # Create a customer with all fields
    create_response = await client.post(
        "/api/customers/",
        json={
            "name": "Full Customer",
            "stakeholders": "Original stakeholders",
            "description": "Original description"
        }
    )
    customer_id = create_response.json()["id"]
    
    # Update only description
    response = await client.put(
        f"/api/customers/{customer_id}",
        json={"description": "Updated description"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Full Customer"
    assert data["stakeholders"] == "Original stakeholders"
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_update_customer_not_found(client: AsyncClient):
    response = await client.put(
        "/api/customers/999",
        json={"name": "Updated Name"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_customer(client: AsyncClient):
    # Create a customer
    create_response = await client.post(
        "/api/customers/",
        json={"name": "Delete Me"}
    )
    customer_id = create_response.json()["id"]
    
    # Delete the customer
    response = await client.delete(f"/api/customers/{customer_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(f"/api/customers/{customer_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_customer_not_found(client: AsyncClient):
    response = await client.delete("/api/customers/999")
    assert response.status_code == 404

