"""Config API for frontend: agent_service_url when set (frontend calls agent_service directly)."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
async def get_config():
    """
    Return client-relevant config. When agent_service_url is set, the frontend
    should call the agent-service directly for chat and RAG search/stats/delete.
    """
    settings = get_settings()
    return {
        "agent_service_url": settings.agent_service_url,
        "user_name": settings.user_name,
        "email": settings.email,
    }
