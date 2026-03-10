"""Health check for backend and load balancers."""

from fastapi import APIRouter

from agent_service.agents.agent_config import get_llm_base_url

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ready",
        "model": get_llm_base_url(),
        "message": "Agent service is running.",
    }
