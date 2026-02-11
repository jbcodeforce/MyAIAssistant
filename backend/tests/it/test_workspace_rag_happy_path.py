"""
Integration test: workspace creation, add knowledge to RAG, query.

Happy path: create a workspace-like directory with sample content,
register and index it via the backend API, then query the RAG and
assert the new knowledge is returned.
"""

import pytest
from httpx import AsyncClient


# Distinctive phrase so the test does not depend on generic wording
INTEGRATION_TEST_UNIQUE_PHRASE = "INTEGRATION_TEST_UNIQUE_PHRASE"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workspace_add_knowledge_and_query_rag_happy_path(
    client: AsyncClient,
    tmp_path,
):
    """
    Full flow: workspace-like dir + sample doc -> create knowledge -> index -> search -> assert.
    """
    # 1. Workspace-like setup: notes/ and sample.md with distinctive content
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    sample_md = notes_dir / "sample.md"
    sample_content = f"""# Integration Test Doc

This document is used by the workspace RAG happy path integration test.
It contains the distinctive phrase: {INTEGRATION_TEST_UNIQUE_PHRASE}.

Some extra context about Python and streaming for semantic search.
"""
    sample_md.write_text(sample_content, encoding="utf-8")
    sample_uri = f"file://{sample_md.resolve()}"

    # 2. Create knowledge
    create_response = await client.post(
        "/api/knowledge/",
        json={
            "title": "Workspace Happy Path Test Doc",
            "document_type": "markdown",
            "uri": sample_uri,
            "category": "integration-test",
            "tags": "integration,rag,workspace",
        },
    )
    assert create_response.status_code == 201
    data = create_response.json()
    knowledge_id = data["id"]

    # 3. Index
    index_response = await client.post(f"/api/rag/index/{knowledge_id}")
    assert index_response.status_code == 200
    index_data = index_response.json()
    assert index_data["success"] is True
    assert index_data["knowledge_id"] == knowledge_id
    assert index_data["chunks_indexed"] > 0
    assert index_data.get("content_hash") is not None

    # 4. Query (phrase that should match the doc)
    search_response = await client.post(
        "/api/rag/search",
        json={"query": INTEGRATION_TEST_UNIQUE_PHRASE, "n_results": 5},
    )
    assert search_response.status_code == 200
    search_data = search_response.json()
    assert search_data["query"] == INTEGRATION_TEST_UNIQUE_PHRASE
    assert search_data["total_results"] >= 1
    assert len(search_data["results"]) >= 1

    # 5. Assert at least one result contains the distinctive phrase
    contents = [r["content"] for r in search_data["results"]]
    assert any(
        INTEGRATION_TEST_UNIQUE_PHRASE in c for c in contents
    ), f"Expected phrase in results: {contents}"
    # Result structure
    first = search_data["results"][0]
    assert "content" in first
    assert "knowledge_id" in first
    assert first["knowledge_id"] == knowledge_id
    assert "title" in first
    assert "score" in first
    assert 0 <= first["score"] <= 1
