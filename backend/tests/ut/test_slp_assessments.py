import pytest
from httpx import AsyncClient


def create_dimension(importance: int = 5, time_spent: int = 5) -> dict:
    """Helper to create a dimension object."""
    return {"importance": importance, "time_spent": time_spent}


def create_full_assessment_data() -> dict:
    """Create a complete assessment data with all dimensions."""
    return {
        "partner": create_dimension(9, 6),
        "family": create_dimension(8, 5),
        "friends": create_dimension(7, 4),
        "physical_health": create_dimension(9, 7),
        "mental_health": create_dimension(9, 6),
        "spirituality": create_dimension(5, 3),
        "community": create_dimension(6, 2),
        "societal": create_dimension(5, 1),
        "job_task": create_dimension(8, 9),
        "learning": create_dimension(8, 5),
        "finance": create_dimension(7, 3),
        "hobbies": create_dimension(7, 4),
        "online_entertainment": create_dimension(4, 6),
        "offline_entertainment": create_dimension(6, 3),
        "physiological_needs": create_dimension(8, 7),
        "daily_activities": create_dimension(6, 5),
    }


@pytest.mark.asyncio
async def test_create_slp_assessment(client: AsyncClient):
    data = create_full_assessment_data()
    response = await client.post("/api/slp-assessments/", json=data)
    
    assert response.status_code == 201
    result = response.json()
    assert "id" in result
    assert "created_at" in result
    assert "updated_at" in result
    assert result["partner"] == data["partner"]
    assert result["family"] == data["family"]
    assert result["physical_health"] == data["physical_health"]


@pytest.mark.asyncio
async def test_create_slp_assessment_missing_field(client: AsyncClient):
    data = create_full_assessment_data()
    del data["partner"]  # Remove a required field
    
    response = await client.post("/api/slp-assessments/", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_slp_assessment_invalid_importance(client: AsyncClient):
    data = create_full_assessment_data()
    data["partner"]["importance"] = 11  # Invalid: must be 0-10
    
    response = await client.post("/api/slp-assessments/", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_slp_assessment_invalid_time_spent(client: AsyncClient):
    data = create_full_assessment_data()
    data["partner"]["time_spent"] = -1  # Invalid: must be 0-10
    
    response = await client.post("/api/slp-assessments/", json=data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_slp_assessments(client: AsyncClient):
    # Create multiple assessments
    for _ in range(3):
        await client.post(
            "/api/slp-assessments/",
            json=create_full_assessment_data()
        )
    
    response = await client.get("/api/slp-assessments/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["assessments"]) == 3
    assert data["skip"] == 0
    assert data["limit"] == 100


@pytest.mark.asyncio
async def test_list_slp_assessments_pagination(client: AsyncClient):
    # Create 5 assessments
    for _ in range(5):
        await client.post(
            "/api/slp-assessments/",
            json=create_full_assessment_data()
        )
    
    # Get first 2
    response = await client.get("/api/slp-assessments/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["assessments"]) == 2
    
    # Get next 2
    response = await client.get("/api/slp-assessments/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["assessments"]) == 2


@pytest.mark.asyncio
async def test_get_slp_assessment(client: AsyncClient):
    # Create an assessment
    create_response = await client.post(
        "/api/slp-assessments/",
        json=create_full_assessment_data()
    )
    assessment_id = create_response.json()["id"]
    
    # Get the assessment
    response = await client.get(f"/api/slp-assessments/{assessment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == assessment_id


@pytest.mark.asyncio
async def test_get_slp_assessment_not_found(client: AsyncClient):
    response = await client.get("/api/slp-assessments/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_slp_assessment(client: AsyncClient):
    # Create an assessment
    create_response = await client.post(
        "/api/slp-assessments/",
        json=create_full_assessment_data()
    )
    assessment_id = create_response.json()["id"]
    original_family = create_response.json()["family"]
    
    # Update only partner dimension
    response = await client.put(
        f"/api/slp-assessments/{assessment_id}",
        json={"partner": {"importance": 10, "time_spent": 10}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["partner"] == {"importance": 10, "time_spent": 10}
    # Other fields should remain unchanged
    assert data["family"] == original_family


@pytest.mark.asyncio
async def test_update_slp_assessment_multiple_fields(client: AsyncClient):
    # Create an assessment
    create_response = await client.post(
        "/api/slp-assessments/",
        json=create_full_assessment_data()
    )
    assessment_id = create_response.json()["id"]
    
    # Update multiple dimensions
    response = await client.put(
        f"/api/slp-assessments/{assessment_id}",
        json={
            "partner": {"importance": 10, "time_spent": 10},
            "learning": {"importance": 0, "time_spent": 0},
            "hobbies": {"importance": 5, "time_spent": 8}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["partner"] == {"importance": 10, "time_spent": 10}
    assert data["learning"] == {"importance": 0, "time_spent": 0}
    assert data["hobbies"] == {"importance": 5, "time_spent": 8}


@pytest.mark.asyncio
async def test_update_slp_assessment_not_found(client: AsyncClient):
    response = await client.put(
        "/api/slp-assessments/999",
        json={"partner": {"importance": 10, "time_spent": 10}}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_slp_assessment_invalid_value(client: AsyncClient):
    # Create an assessment
    create_response = await client.post(
        "/api/slp-assessments/",
        json=create_full_assessment_data()
    )
    assessment_id = create_response.json()["id"]
    
    # Try to update with invalid value
    response = await client.put(
        f"/api/slp-assessments/{assessment_id}",
        json={"partner": {"importance": 15, "time_spent": 5}}  # 15 is out of range
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_slp_assessment(client: AsyncClient):
    # Create an assessment
    create_response = await client.post(
        "/api/slp-assessments/",
        json=create_full_assessment_data()
    )
    assessment_id = create_response.json()["id"]
    
    # Delete the assessment
    response = await client.delete(f"/api/slp-assessments/{assessment_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(f"/api/slp-assessments/{assessment_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_slp_assessment_not_found(client: AsyncClient):
    response = await client.delete("/api/slp-assessments/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_dimension_boundary_values(client: AsyncClient):
    """Test boundary values 0 and 10 for dimensions."""
    data = create_full_assessment_data()
    # Set partner to minimum values
    data["partner"] = {"importance": 0, "time_spent": 0}
    # Set family to maximum values
    data["family"] = {"importance": 10, "time_spent": 10}
    
    response = await client.post("/api/slp-assessments/", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["partner"] == {"importance": 0, "time_spent": 0}
    assert result["family"] == {"importance": 10, "time_spent": 10}


@pytest.mark.asyncio
async def test_assessment_has_timestamps(client: AsyncClient):
    """Verify that assessments have proper timestamps."""
    response = await client.post(
        "/api/slp-assessments/",
        json=create_full_assessment_data()
    )
    assert response.status_code == 201
    data = response.json()
    
    assert "created_at" in data
    assert "updated_at" in data
    assert data["created_at"] is not None
    assert data["updated_at"] is not None

