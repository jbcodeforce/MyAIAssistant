"""Pytest fixtures for agent_service integration tests."""

import json
import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

# Avoid importing agent_service (slow Chroma/Ollama) unless live tests requested
_LIVE = os.environ.get("AGENT_SERVICE_LIVE") == "1"

# Use the real app only when AGENT_SERVICE_LIVE=1 so CI can run fast by default.
# When unset, use a minimal app that matches the same HTTP contract (paths, shapes).
def _make_app():
    if _LIVE:
        from agent_service.main import app
        return app
    app = FastAPI(title="Agent Service Test")

    @app.get("/")
    async def root():
        return {"service": "agent-service", "message": "Agno + AgentOS; use /health, /chat/todo, /chat/generic"}

    @app.get("/health")
    async def health():
        return {"status": "ready", "model": "test-model", "message": "Agent service is running."}

    @app.post("/chat/todo")
    async def chat_todo(request: dict):
        return {"message": "Test response.", "context_used": []}

    @app.post("/chat/generic")
    async def chat_generic(request: dict):
        return {"message": "Test response.", "context_used": []}

    @app.post("/chat/generic/stream")
    async def chat_generic_stream(request: dict):
        def gen():
            yield json.dumps({"content": "Test"}) + "\n"
            yield json.dumps({"done": True}) + "\n"
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            (line.encode("utf-8") for line in gen()),
            media_type="application/x-ndjson",
        )

    @app.post("/rag/index/{knowledge_id}")
    async def rag_index(knowledge_id: int, payload: dict):
        if not (payload.get("content") or "").strip():
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="content is required")
        return {"success": True, "knowledge_id": knowledge_id, "chunks_indexed": 1}

    @app.post("/rag/search")
    async def rag_search(payload: dict):
        return {"query": payload.get("query", ""), "results": [], "total_results": 0}

    @app.get("/rag/search")
    async def rag_search_get(q: str, n: int = 5):
        return {"query": q, "results": [], "total_results": 0}

    @app.get("/rag/stats")
    async def rag_stats():
        return {"total_chunks": 0, "unique_knowledge_items": 0, "collection_name": "knowledge_base", "embedding_model": "ollama"}

    @app.delete("/rag/index/{knowledge_id}")
    async def rag_remove(knowledge_id: int):
        return {"message": f"Successfully removed index for knowledge item {knowledge_id}"}

    @app.post("/extract/meeting")
    async def extract_meeting(request: dict):
        return {
            "attendees": [],
            "next_steps": [],
            "key_points": [],
            "cleaned_notes": request.get("content", "")[:200],
        }

    @app.post("/tag/task")
    async def tag_task(request: dict):
        return {"message": "Suggested tags.", "tags": ["test"]}

    return app


@pytest_asyncio.fixture
async def client():
    """Async HTTP client against the agent_service (or contract-equivalent test) app."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
    ) as ac:
        yield ac
