"""Unit tests for RAG index proxy (agent-service required)."""

import os
import tempfile

import pytest
from httpx import AsyncClient


@pytest.fixture
def sample_markdown_file():
    """Create a temporary markdown file for testing."""
    content = """# Test Document

This is a test document for the RAG index proxy.
It contains Python programming keywords for loading tests.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        f.flush()
        path = f.name
    yield path
    os.unlink(path)


@pytest.mark.asyncio
async def test_rag_stats_redirects_to_agent_service(client: AsyncClient):
    response = await client.get("/api/rag/stats")
    assert response.status_code == 503
    assert "agent_service" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rag_search_redirects_to_agent_service(client: AsyncClient):
    response = await client.get("/api/rag/search?q=test&n=5")
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_rag_search_post_redirects_to_agent_service(client: AsyncClient):
    response = await client.post("/api/rag/search", json={"query": "test", "n_results": 5})
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_rag_index_not_found(client: AsyncClient):
    response = await client.post("/api/rag/index/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge item not found"


@pytest.mark.asyncio
async def test_rag_remove_index_redirects_to_agent_service(client: AsyncClient):
    response = await client.delete("/api/rag/index/9999")
    assert response.status_code == 503


@pytest.mark.asyncio
async def test_rag_index_knowledge_with_file(client: AsyncClient, sample_markdown_file: str):
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "RAG Test Document",
            "document_type": "markdown",
            "uri": f"file://{sample_markdown_file}",
            "category": "Testing",
            "tags": "rag,test",
        },
    )
    assert create_response.status_code == 201
    knowledge_id = create_response.json()["id"]

    index_response = await client.post(f"/api/rag/index/{knowledge_id}")
    assert index_response.status_code == 200
    data = index_response.json()
    assert data["success"] is True
    assert data["knowledge_id"] == knowledge_id
    assert data["chunks_indexed"] == 5
    assert data["content_hash"] == "deadbeef"


@pytest.mark.asyncio
async def test_rag_index_all(client: AsyncClient, sample_markdown_file: str):
    for i in range(3):
        await client.post(
            "/api/knowledge/",
            json={
                "title": f"Bulk Index Test {i}",
                "document_type": "markdown",
                "uri": f"file://{sample_markdown_file}",
                "status": "active",
            },
        )

    index_response = await client.post("/api/rag/index-all?status=active")
    assert index_response.status_code == 200
    data = index_response.json()
    assert data["total_items"] >= 3
    assert data["successful"] >= 3
    assert data["failed"] == 0


@pytest.mark.asyncio
async def test_rag_index_updates_knowledge_status(client: AsyncClient, sample_markdown_file: str):
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Status Update Test",
            "document_type": "markdown",
            "uri": f"file://{sample_markdown_file}",
            "status": "pending",
        },
    )
    knowledge_id = create_response.json()["id"]

    await client.post(f"/api/rag/index/{knowledge_id}")

    get_response = await client.get(f"/api/knowledge/{knowledge_id}")
    data = get_response.json()
    assert data["status"] == "active"
    assert data["content_hash"] is not None
    assert data["last_fetched_at"] is not None


@pytest.mark.asyncio
async def test_rag_index_invalid_file(client: AsyncClient):
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Invalid File Test",
            "document_type": "markdown",
            "uri": "file:///nonexistent/path/file.md",
        },
    )
    knowledge_id = create_response.json()["id"]

    index_response = await client.post(f"/api/rag/index/{knowledge_id}")
    assert index_response.status_code == 200
    data = index_response.json()
    assert data["success"] is False
    assert data["error"] == "No documents loaded"
