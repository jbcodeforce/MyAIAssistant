"""HTTP client for the agent-service (Agno/AgentOS). Used when agent_service_url is set."""

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return get_settings().agent_service_url.rstrip("/")


async def health() -> dict[str, Any]:
    """GET /health from agent-service."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{_base_url()}/health")
        r.raise_for_status()
        return r.json()


async def chat_todo(
    message: str,
    conversation_history: list[dict],
    task_title: str | None = None,
    task_description: str | None = None,
    use_rag: bool = True,
) -> dict[str, Any]:
    """POST /chat/todo to agent-service."""
    body = {
        "message": message,
        "conversation_history": conversation_history,
        "use_rag": use_rag,
    }
    if task_title is not None:
        body["task_title"] = task_title
    if task_description is not None:
        body["task_description"] = task_description
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{_base_url()}/chat/todo", json=body)
        r.raise_for_status()
        return r.json()


async def chat_generic(
    message: str,
    conversation_history: list[dict],
    context: dict | None = None,
    force_intent: str | None = None,
) -> dict[str, Any]:
    """POST /chat/generic to agent-service."""
    body = {
        "message": message,
        "conversation_history": conversation_history,
    }
    if context:
        body["context"] = context
    if force_intent:
        body["force_intent"] = force_intent
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{_base_url()}/chat/generic", json=body)
        r.raise_for_status()
        return r.json()


async def chat_generic_stream(
    message: str,
    conversation_history: list[dict],
    context: dict | None = None,
    force_intent: str | None = None,
):
    """POST /chat/generic/stream to agent-service; yields NDJSON lines."""
    body = {
        "message": message,
        "conversation_history": conversation_history,
    }
    if context:
        body["context"] = context
    if force_intent:
        body["force_intent"] = force_intent
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", f"{_base_url()}/chat/generic/stream", json=body) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    yield line


async def rag_index(
    knowledge_id: int,
    title: str,
    uri: str,
    document_type: str,
    content: str,
    category: str | None = None,
    tags: str | None = None,
) -> dict[str, Any]:
    """POST /rag/index/{knowledge_id} to agent-service with preloaded content."""
    body = {
        "title": title,
        "uri": uri,
        "document_type": document_type,
        "content": content,
    }
    if category is not None:
        body["category"] = category
    if tags is not None:
        body["tags"] = tags
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{_base_url()}/rag/index/{knowledge_id}", json=body)
        r.raise_for_status()
        return r.json()


async def rag_search(
    query: str,
    n_results: int = 5,
    category: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """POST /rag/search to agent-service."""
    body = {"query": query, "n_results": n_results}
    if category is not None:
        body["category"] = category
    if tags is not None:
        body["tags"] = tags
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{_base_url()}/rag/search", json=body)
        r.raise_for_status()
        return r.json()


async def rag_search_get(q: str, n: int = 5, category: str | None = None) -> dict[str, Any]:
    """GET /rag/search to agent-service."""
    params = {"q": q, "n": n}
    if category is not None:
        params["category"] = category
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{_base_url()}/rag/search", params=params)
        r.raise_for_status()
        return r.json()


async def rag_stats() -> dict[str, Any]:
    """GET /rag/stats from agent-service."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{_base_url()}/rag/stats")
        r.raise_for_status()
        return r.json()


async def rag_remove_index(knowledge_id: int) -> None:
    """DELETE /rag/index/{knowledge_id} on agent-service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.delete(f"{_base_url()}/rag/index/{knowledge_id}")
        r.raise_for_status()


async def extract_meeting(
    content: str,
    organization: str | None = None,
    project: str | None = None,
    attendees: str | None = None,
) -> dict[str, Any]:
    """POST /extract/meeting to agent-service."""
    body = {"content": content}
    if organization is not None:
        body["organization"] = organization
    if project is not None:
        body["project"] = project
    if attendees is not None:
        body["attendees"] = attendees
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{_base_url()}/extract/meeting", json=body)
        r.raise_for_status()
        return r.json()


async def tag_task(
    task_title: str,
    task_description: str | None = None,
) -> dict[str, Any]:
    """POST /tag/task to agent-service."""
    body = {"task_title": task_title}
    if task_description is not None:
        body["task_description"] = task_description
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{_base_url()}/tag/task", json=body)
        r.raise_for_status()
        return r.json()
