"""Compatibility routes for backend proxy (chat, health, rag, extract, tag)."""

from agent_service.routes.chat import router as chat_router
from agent_service.routes.health import router as health_router
from agent_service.routes.rag import router as rag_router
from agent_service.routes.extract import router as extract_router
from agent_service.routes.tag import router as tag_router

__all__ = ["chat_router", "health_router", "rag_router", "extract_router", "tag_router"]
