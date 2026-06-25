"""Chat API endpoints. Chat runs on agent-service; these routes return health or 503."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import get_db
from app.services import agent_service_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _agent_service_required():
    agent_service_client.require_agent_service_url()


@router.post("/todo/{todo_id}")
async def chat_about_todo(todo_id: int, http_request: Request, db: AsyncSession = Depends(get_db)):
    """Chat about a todo runs on agent-service (POST /chat/todo after fetching todo)."""
    _agent_service_required()
    raise HTTPException(
        status_code=503,
        detail="Use agent_service_url for chat (frontend calls agent-service directly)",
    )


@router.post("/generic")
async def generic_chat(http_request: Request):
    """Generic chat runs on agent-service."""
    _agent_service_required()
    raise HTTPException(
        status_code=503,
        detail="Use agent_service_url for chat (frontend calls agent-service directly)",
    )


@router.post("/generic/stream")
async def generic_chat_stream(http_request: Request, db: AsyncSession = Depends(get_db)):
    """Streamed generic chat runs on agent-service."""
    _agent_service_required()
    raise HTTPException(
        status_code=503,
        detail="Use agent_service_url for chat (frontend calls agent-service directly)",
    )


@router.post("/kb")
async def kb_chat(http_request: Request):
    """Knowledge-base chat runs on agent-service."""
    _agent_service_required()
    raise HTTPException(
        status_code=503,
        detail="Use agent_service_url for chat (frontend calls agent-service directly)",
    )


@router.get("/health")
async def chat_health_check():
    """Return agent_service_url so the frontend can call agent-service for chat and RAG."""
    settings = get_settings()
    out = {"agent_service_url": settings.agent_service_url}
    if settings.agent_service_url:
        out["status"] = "agent_service"
        out["message"] = "Frontend should call agent_service_url for chat and RAG search/stats."
        return out
    out["status"] = "not_configured"
    out["message"] = "Set agent_service_url to enable chat and RAG."
    return out
