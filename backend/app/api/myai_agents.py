"""Proxy to agent-service GET /myai/agents for the Vue Agents and Assistant pickers."""

import logging

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.services.agent_service_client import list_myai_agents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/myai", tags=["myai"])


@router.get("/agents")
async def get_myai_agents():
    """
    List agents from the agent microservice. Uses server-side ``agent_service_url`` so
    the browser does not need to reach the agent service directly.
    """
    if not (get_settings().agent_service_url or "").strip():
        raise HTTPException(
            status_code=503,
            detail="agent_service_url is not configured",
        )
    try:
        return await list_myai_agents()
    except httpx.HTTPStatusError as e:
        logger.warning("Agent service /myai/agents returned %s: %s", e.response.status_code, e)
        raise HTTPException(
            status_code=502,
            detail="Agent service returned an error for /myai/agents",
        ) from e
    except httpx.RequestError as e:
        logger.exception("Agent service unreachable for /myai/agents")
        raise HTTPException(
            status_code=502,
            detail="Agent service unreachable",
        ) from e
