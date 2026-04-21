"""HTTP client for the agent-service. Used by backend for RAG index, meeting extract, and task tag. Chat and RAG search/stats/delete are called directly by the frontend when agent_service_url is set."""

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return get_settings().agent_service_url.rstrip("/")


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
