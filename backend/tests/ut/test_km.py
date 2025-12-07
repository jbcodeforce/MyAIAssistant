import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_knowledge(client: AsyncClient):
    """Test creating a new knowledge item."""
    response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Test Documentation",
            "description": "This is a test knowledge item",
            "document_type": "markdown",
            "uri": "file:///docs/test.md",
            "category": "Documentation",
            "tags": "python,backend,api",
            "status": "active"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Documentation"
    assert data["description"] == "This is a test knowledge item"
    assert data["document_type"] == "markdown"
    assert data["uri"] == "file:///docs/test.md"
    assert data["category"] == "Documentation"
    assert data["tags"] == "python,backend,api"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "referenced_at" in data


@pytest.mark.asyncio
async def test_create_knowledge_minimal(client: AsyncClient):
    """Test creating a knowledge item with only required fields."""
    response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Minimal Item",
            "document_type": "website",
            "uri": "https://example.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Item"
    assert data["document_type"] == "website"
    assert data["uri"] == "https://example.com"
    assert data["status"] == "active"  # default value
    assert data["category"] is None
    assert data["tags"] is None
    assert data["description"] is None


@pytest.mark.asyncio
async def test_create_knowledge_tag_normalization(client: AsyncClient):
    """Test that tags are normalized (trimmed, lowercased, deduplicated)."""
    response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Tag Test",
            "document_type": "markdown",
            "uri": "file:///test.md",
            "tags": "  Python , BACKEND,  python, API  "
        }
    )
    assert response.status_code == 201
    data = response.json()
    # Tags should be normalized: trimmed, lowercased, duplicates removed
    assert data["tags"] == "python,backend,api"


@pytest.mark.asyncio
async def test_list_knowledge(client: AsyncClient):
    """Test listing knowledge items."""
    # Create a few knowledge items
    for i in range(3):
        await client.post(
            "/api/knowledge/",
            json={
                "title": f"Test Item {i}",
                "document_type": "markdown",
                "uri": f"file:///test{i}.md"
            }
        )
    
    response = await client.get("/api/knowledge/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_knowledge_pagination(client: AsyncClient):
    """Test pagination of knowledge items."""
    # Create 5 items
    for i in range(5):
        await client.post(
            "/api/knowledge/",
            json={
                "title": f"Test Item {i}",
                "document_type": "markdown",
                "uri": f"file:///test{i}.md"
            }
        )
    
    # Get first page with limit 2
    response = await client.get("/api/knowledge/?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 0
    assert data["limit"] == 2
    
    # Get second page
    response = await client.get("/api/knowledge/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 2


@pytest.mark.asyncio
async def test_list_knowledge_filter_by_document_type(client: AsyncClient):
    """Test filtering knowledge items by document type."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Markdown Doc",
            "document_type": "markdown",
            "uri": "file:///test.md"
        }
    )
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Website Doc",
            "document_type": "website",
            "uri": "https://example.com"
        }
    )
    
    response = await client.get("/api/knowledge/?document_type=markdown")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["document_type"] == "markdown"


@pytest.mark.asyncio
async def test_list_knowledge_filter_by_status(client: AsyncClient):
    """Test filtering knowledge items by status."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Active Item",
            "document_type": "markdown",
            "uri": "file:///active.md",
            "status": "active"
        }
    )
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Archived Item",
            "document_type": "markdown",
            "uri": "file:///archived.md",
            "status": "archived"
        }
    )
    
    response = await client.get("/api/knowledge/?status=active")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_list_knowledge_filter_by_multiple_statuses(client: AsyncClient):
    """Test filtering by multiple comma-separated statuses."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Active Item",
            "document_type": "markdown",
            "uri": "file:///active.md",
            "status": "active"
        }
    )
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Pending Item",
            "document_type": "markdown",
            "uri": "file:///pending.md",
            "status": "pending"
        }
    )
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Archived Item",
            "document_type": "markdown",
            "uri": "file:///archived.md",
            "status": "archived"
        }
    )
    
    response = await client.get("/api/knowledge/?status=active,pending")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_knowledge_filter_by_category(client: AsyncClient):
    """Test filtering knowledge items by category."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Doc Item",
            "document_type": "markdown",
            "uri": "file:///doc.md",
            "category": "Documentation"
        }
    )
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Ref Item",
            "document_type": "markdown",
            "uri": "file:///ref.md",
            "category": "Reference"
        }
    )
    
    response = await client.get("/api/knowledge/?category=Documentation")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "Documentation"


@pytest.mark.asyncio
async def test_list_knowledge_filter_by_tag(client: AsyncClient):
    """Test filtering knowledge items by tag."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Python Doc",
            "document_type": "markdown",
            "uri": "file:///python.md",
            "tags": "python,backend"
        }
    )
    await client.post(
        "/api/knowledge/",
        json={
            "title": "JS Doc",
            "document_type": "markdown",
            "uri": "file:///js.md",
            "tags": "javascript,frontend"
        }
    )
    
    response = await client.get("/api/knowledge/?tag=python")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "python" in data["items"][0]["tags"]


@pytest.mark.asyncio
async def test_list_knowledge_filter_by_tag_in_middle(client: AsyncClient):
    """Test filtering by tag that appears in the middle of the tags string."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Multi Tag Doc",
            "document_type": "markdown",
            "uri": "file:///multi.md",
            "tags": "python,backend,api"
        }
    )
    
    response = await client.get("/api/knowledge/?tag=backend")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_knowledge_combined_filters(client: AsyncClient):
    """Test combining multiple filters."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Active Markdown Python",
            "document_type": "markdown",
            "uri": "file:///test1.md",
            "status": "active",
            "category": "Documentation",
            "tags": "python"
        }
    )
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Active Website Python",
            "document_type": "website",
            "uri": "https://example.com",
            "status": "active",
            "category": "Documentation",
            "tags": "python"
        }
    )
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Archived Markdown Python",
            "document_type": "markdown",
            "uri": "file:///test2.md",
            "status": "archived",
            "category": "Documentation",
            "tags": "python"
        }
    )
    
    response = await client.get(
        "/api/knowledge/?document_type=markdown&status=active&category=Documentation&tag=python"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Active Markdown Python"


@pytest.mark.asyncio
async def test_get_knowledge(client: AsyncClient):
    """Test retrieving a specific knowledge item by ID."""
    # Create a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Test Item",
            "document_type": "markdown",
            "uri": "file:///test.md",
            "category": "Testing"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Get the item
    response = await client.get(f"/api/knowledge/{knowledge_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == knowledge_id
    assert data["title"] == "Test Item"
    assert data["category"] == "Testing"


@pytest.mark.asyncio
async def test_get_knowledge_not_found(client: AsyncClient):
    """Test retrieving a non-existent knowledge item."""
    response = await client.get("/api/knowledge/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge item not found"


@pytest.mark.asyncio
async def test_update_knowledge(client: AsyncClient):
    """Test updating a knowledge item."""
    # Create a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Original Title",
            "document_type": "markdown",
            "uri": "file:///test.md",
            "status": "active"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Update the item
    response = await client.put(
        f"/api/knowledge/{knowledge_id}",
        json={
            "title": "Updated Title",
            "category": "Updated Category",
            "tags": "new,tags"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["category"] == "Updated Category"
    assert data["tags"] == "new,tags"
    # Unchanged fields should remain
    assert data["document_type"] == "markdown"
    assert data["uri"] == "file:///test.md"


@pytest.mark.asyncio
async def test_update_knowledge_status(client: AsyncClient):
    """Test updating the status of a knowledge item."""
    # Create a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Test Item",
            "document_type": "markdown",
            "uri": "file:///test.md",
            "status": "active"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Update to archived
    response = await client.put(
        f"/api/knowledge/{knowledge_id}",
        json={"status": "archived"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "archived"


@pytest.mark.asyncio
async def test_update_knowledge_content_hash(client: AsyncClient):
    """Test updating the content hash of a knowledge item."""
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Test Item",
            "document_type": "markdown",
            "uri": "file:///test.md"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Update content hash
    test_hash = "abc123def456" * 4  # 48 chars, simulating a hash
    response = await client.put(
        f"/api/knowledge/{knowledge_id}",
        json={"content_hash": test_hash}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content_hash"] == test_hash


@pytest.mark.asyncio
async def test_update_knowledge_not_found(client: AsyncClient):
    """Test updating a non-existent knowledge item."""
    response = await client.put(
        "/api/knowledge/999",
        json={"title": "Updated Title"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge item not found"


@pytest.mark.asyncio
async def test_update_knowledge_tag_normalization(client: AsyncClient):
    """Test that tags are normalized during update."""
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Test Item",
            "document_type": "markdown",
            "uri": "file:///test.md"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Update with tags that need normalization
    response = await client.put(
        f"/api/knowledge/{knowledge_id}",
        json={"tags": "  PYTHON , backend, PYTHON "}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == "python,backend"


@pytest.mark.asyncio
async def test_delete_knowledge(client: AsyncClient):
    """Test deleting a knowledge item."""
    # Create a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Test Item",
            "document_type": "markdown",
            "uri": "file:///test.md"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Delete the item
    response = await client.delete(f"/api/knowledge/{knowledge_id}")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(f"/api/knowledge/{knowledge_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_knowledge_not_found(client: AsyncClient):
    """Test deleting a non-existent knowledge item."""
    response = await client.delete("/api/knowledge/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge item not found"


@pytest.mark.asyncio
async def test_create_knowledge_validation_missing_title(client: AsyncClient):
    """Test validation when title is missing."""
    response = await client.post(
        "/api/knowledge/",
        json={
            "document_type": "markdown",
            "uri": "file:///test.md"
        }
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_knowledge_validation_missing_document_type(client: AsyncClient):
    """Test validation when document_type is missing."""
    response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Test",
            "uri": "file:///test.md"
        }
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_knowledge_validation_missing_uri(client: AsyncClient):
    """Test validation when uri is missing."""
    response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Test",
            "document_type": "markdown"
        }
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_knowledge_validation_title_too_long(client: AsyncClient):
    """Test validation when title exceeds max length."""
    response = await client.post(
        "/api/knowledge/",
        json={
            "title": "x" * 256,  # max is 255
            "document_type": "markdown",
            "uri": "file:///test.md"
        }
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_knowledge_empty(client: AsyncClient):
    """Test listing when no knowledge items exist."""
    response = await client.get("/api/knowledge/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["skip"] == 0
    assert data["limit"] == 100


@pytest.mark.asyncio
async def test_list_knowledge_ordering(client: AsyncClient):
    """Test that knowledge items are returned ordered by created_at descending."""
    # Create items with distinct titles
    titles = ["First", "Second", "Third"]
    for title in titles:
        await client.post(
            "/api/knowledge/",
            json={
                "title": title,
                "document_type": "markdown",
                "uri": f"file:///{title.lower()}.md"
            }
        )
    
    response = await client.get("/api/knowledge/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    
    # Verify all items are returned
    returned_titles = {item["title"] for item in data["items"]}
    assert returned_titles == {"First", "Second", "Third"}
    
    # Verify items are ordered by created_at descending (or same timestamp)
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["created_at"] >= items[i + 1]["created_at"]


@pytest.mark.asyncio
async def test_update_knowledge_partial(client: AsyncClient):
    """Test partial update - only specified fields should change."""
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Original",
            "description": "Original description",
            "document_type": "markdown",
            "uri": "file:///test.md",
            "category": "Original Category",
            "tags": "original,tags",
            "status": "active"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Update only title
    response = await client.put(
        f"/api/knowledge/{knowledge_id}",
        json={"title": "Updated"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    # Other fields unchanged
    assert data["description"] == "Original description"
    assert data["category"] == "Original Category"
    assert data["tags"] == "original,tags"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_knowledge_timestamps(client: AsyncClient):
    """Test that timestamps are properly set and updated."""
    # Create item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Timestamp Test",
            "document_type": "markdown",
            "uri": "file:///test.md"
        }
    )
    assert create_response.status_code == 201
    data = create_response.json()
    assert data["created_at"] is not None
    assert data["updated_at"] is not None
    assert data["referenced_at"] is not None
    assert data["last_fetched_at"] is None  # Not set on creation


@pytest.mark.asyncio
async def test_filter_by_tag_single_tag_item(client: AsyncClient):
    """Test filtering by tag when item has only one tag."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Single Tag",
            "document_type": "markdown",
            "uri": "file:///single.md",
            "tags": "python"
        }
    )
    
    response = await client.get("/api/knowledge/?tag=python")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_filter_by_tag_at_start(client: AsyncClient):
    """Test filtering by tag at the start of tags string."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Tags at start",
            "document_type": "markdown",
            "uri": "file:///start.md",
            "tags": "python,backend,api"
        }
    )
    
    response = await client.get("/api/knowledge/?tag=python")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_filter_by_tag_at_end(client: AsyncClient):
    """Test filtering by tag at the end of tags string."""
    await client.post(
        "/api/knowledge/",
        json={
            "title": "Tags at end",
            "document_type": "markdown",
            "uri": "file:///end.md",
            "tags": "python,backend,api"
        }
    )
    
    response = await client.get("/api/knowledge/?tag=api")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

