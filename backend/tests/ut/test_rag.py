"""Unit tests for RAG functionality."""

import pytest
from httpx import AsyncClient
import tempfile
import os


@pytest.fixture
def sample_markdown_file():
    """Create a temporary markdown file for testing."""
    content = """# Test Document

## Introduction

This is a test document for the RAG system. It contains multiple sections
to test the chunking and embedding functionality.

## Section One

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
consequat.

## Section Two

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident,
sunt in culpa qui officia deserunt mollit anim id est laborum.

## Technical Details

This section contains technical information about Python programming:

```python
def hello_world():
    print("Hello, World!")
```

## Conclusion

This concludes the test document for RAG functionality testing.
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.mark.asyncio
async def test_rag_stats_empty(client: AsyncClient):
    """Test getting RAG stats when no documents are indexed."""
    response = await client.get("/api/rag/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_chunks" in data
    assert "unique_knowledge_items" in data
    assert "collection_name" in data
    assert "embedding_model" in data


@pytest.mark.asyncio
async def test_rag_search_empty(client: AsyncClient):
    """Test searching when no documents are indexed."""
    response = await client.get("/api/rag/search?q=test&n=5")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert data["results"] == []
    assert data["total_results"] == 0


@pytest.mark.asyncio
async def test_rag_search_post_empty(client: AsyncClient):
    """Test POST search when no documents are indexed."""
    response = await client.post(
        "/api/rag/search",
        json={"query": "test", "n_results": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test"
    assert data["results"] == []


@pytest.mark.asyncio
async def test_rag_index_not_found(client: AsyncClient):
    """Test indexing a non-existent knowledge item."""
    response = await client.post("/api/rag/index/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge item not found"


@pytest.mark.asyncio
async def test_rag_remove_index_not_found(client: AsyncClient):
    """Test removing index for non-existent knowledge item."""
    response = await client.delete("/api/rag/index/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_rag_index_knowledge_with_file(client: AsyncClient, sample_markdown_file: str):
    """Test indexing a knowledge item with a real file."""
    # Create a knowledge item pointing to the test file
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "RAG Test Document",
            "document_type": "markdown",
            "uri": f"file://{sample_markdown_file}",
            "category": "Testing",
            "tags": "rag,test,embedding"
        }
    )
    assert create_response.status_code == 201
    knowledge_id = create_response.json()["id"]
    
    # Index the document
    index_response = await client.post(f"/api/rag/index/{knowledge_id}")
    assert index_response.status_code == 200
    data = index_response.json()
    assert data["success"] is True
    assert data["knowledge_id"] == knowledge_id
    assert data["chunks_indexed"] > 0
    assert data["content_hash"] is not None
    
    # Check stats
    stats_response = await client.get("/api/rag/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total_chunks"] > 0
    assert stats["unique_knowledge_items"] >= 1


@pytest.mark.asyncio
async def test_rag_search_after_indexing(client: AsyncClient, sample_markdown_file: str):
    """Test searching after indexing a document."""
    # Create and index a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Search Test Document",
            "document_type": "markdown",
            "uri": f"file://{sample_markdown_file}",
            "category": "SearchTest"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    await client.post(f"/api/rag/index/{knowledge_id}")
    
    # Search for content in the document
    search_response = await client.get("/api/rag/search?q=Python+programming&n=3")
    assert search_response.status_code == 200
    data = search_response.json()
    assert data["total_results"] > 0
    
    # Check result structure
    for result in data["results"]:
        assert "content" in result
        assert "knowledge_id" in result
        assert "title" in result
        assert "score" in result
        assert result["score"] >= 0 and result["score"] <= 1


@pytest.mark.asyncio
async def test_rag_search_with_category_filter(client: AsyncClient, sample_markdown_file: str):
    """Test searching with category filter."""
    # Create and index a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Category Filter Test",
            "document_type": "markdown",
            "uri": f"file://{sample_markdown_file}",
            "category": "UniqueCategory"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    await client.post(f"/api/rag/index/{knowledge_id}")
    
    # Search with matching category
    search_response = await client.get("/api/rag/search?q=test&category=UniqueCategory")
    assert search_response.status_code == 200
    data = search_response.json()
    # Results should only include items from this category
    for result in data["results"]:
        assert result["knowledge_id"] == knowledge_id


@pytest.mark.asyncio
async def test_rag_remove_index(client: AsyncClient, sample_markdown_file: str):
    """Test removing a knowledge item from the index."""
    # Create and index a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Remove Index Test",
            "document_type": "markdown",
            "uri": f"file://{sample_markdown_file}"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Index the document
    await client.post(f"/api/rag/index/{knowledge_id}")
    
    # Get stats before removal
    stats_before = await client.get("/api/rag/stats")
    chunks_before = stats_before.json()["total_chunks"]
    
    # Remove from index
    remove_response = await client.delete(f"/api/rag/index/{knowledge_id}")
    assert remove_response.status_code == 200
    
    # Get stats after removal
    stats_after = await client.get("/api/rag/stats")
    chunks_after = stats_after.json()["total_chunks"]
    
    # Should have fewer chunks
    assert chunks_after < chunks_before


@pytest.mark.asyncio
async def test_rag_index_all(client: AsyncClient, sample_markdown_file: str):
    """Test indexing all knowledge items."""
    # Create multiple knowledge items
    for i in range(3):
        await client.post(
            "/api/knowledge/",
            json={
                "title": f"Bulk Index Test {i}",
                "document_type": "markdown",
                "uri": f"file://{sample_markdown_file}",
                "status": "active"
            }
        )
    
    # Index all
    index_response = await client.post("/api/rag/index-all?status=active")
    assert index_response.status_code == 200
    data = index_response.json()
    assert data["total_items"] >= 3
    assert data["successful"] >= 3
    assert data["failed"] == 0


@pytest.mark.asyncio
async def test_rag_index_updates_knowledge_status(client: AsyncClient, sample_markdown_file: str):
    """Test that indexing updates the knowledge item status and hash."""
    # Create a knowledge item
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Status Update Test",
            "document_type": "markdown",
            "uri": f"file://{sample_markdown_file}",
            "status": "pending"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Index the document
    await client.post(f"/api/rag/index/{knowledge_id}")
    
    # Get the updated knowledge item
    get_response = await client.get(f"/api/knowledge/{knowledge_id}")
    data = get_response.json()
    
    # Status should be updated to active
    assert data["status"] == "active"
    # Content hash should be set
    assert data["content_hash"] is not None
    # Last fetched should be set
    assert data["last_fetched_at"] is not None


@pytest.mark.asyncio
async def test_rag_index_invalid_file(client: AsyncClient):
    """Test indexing a knowledge item with invalid file path."""
    # Create a knowledge item with non-existent file
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Invalid File Test",
            "document_type": "markdown",
            "uri": "file:///nonexistent/path/file.md"
        }
    )
    knowledge_id = create_response.json()["id"]
    
    # Index the document - should fail gracefully
    index_response = await client.post(f"/api/rag/index/{knowledge_id}")
    assert index_response.status_code == 200
    data = index_response.json()
    assert data["success"] is False
    assert data["error"] is not None
    assert "not found" in data["error"].lower()

