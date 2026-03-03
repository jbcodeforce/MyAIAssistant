"""Health check for backend and load balancers."""

from fastapi import APIRouter

from agent_service.config import get_llm_model

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ready",
        "model": get_llm_model(),
        "message": "Agent service is running.",
    }
