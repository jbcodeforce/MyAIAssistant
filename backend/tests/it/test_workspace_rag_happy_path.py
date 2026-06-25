"""
Integration test: workspace creation and RAG index via backend proxy.

Search/query runs on agent-service directly (not backend /api/rag/search).
"""

import pytest
from httpx import AsyncClient

INTEGRATION_TEST_UNIQUE_PHRASE = "INTEGRATION_TEST_UNIQUE_PHRASE"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_workspace_add_knowledge_and_index_via_backend(
    client: AsyncClient,
    tmp_path,
):
    """Create knowledge from workspace file and index through backend -> agent-service proxy."""
    notes_dir = tmp_path / "notes"
    notes_dir.mkdir()
    sample_md = notes_dir / "sample.md"
    sample_content = f"""# Integration Test Doc

This document is used by the workspace RAG happy path integration test.
It contains the distinctive phrase: {INTEGRATION_TEST_UNIQUE_PHRASE}.
"""
    sample_md.write_text(sample_content, encoding="utf-8")
    sample_uri = f"file://{sample_md.resolve()}"

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
    knowledge_id = create_response.json()["id"]

    index_response = await client.post(f"/api/rag/index/{knowledge_id}")
    assert index_response.status_code == 200
    index_data = index_response.json()
    assert index_data["success"] is True
    assert index_data["knowledge_id"] == knowledge_id
    assert index_data.get("content_hash") is not None
