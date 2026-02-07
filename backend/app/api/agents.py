import logging

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings, resolve_agent_config_dir
from app.api.schemas.agent import AgentConfigResponse
from agent_core.agents.agent_factory import get_agent_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/", response_model=list[AgentConfigResponse])
async def list_agents():
    """
    List configured agents (read-only). Data comes from the agent config directory, no database.
    """
    try:
        settings = get_settings()
        config_dir = resolve_agent_config_dir(settings.agent_config_dir)
        factory = get_agent_factory(config_dir=config_dir)
    except Exception as e:
        logger.exception("Failed to get agent factory")
        raise HTTPException(status_code=503, detail="Agent configuration unavailable") from e

    result = []
    for name in factory.list_agents():
        config = factory.get_config(name)
        if config is None:
            continue
        result.append(
            AgentConfigResponse(
                name=config.name,
                description=config.description or "",
                model=config.model,
                agent_class=config.agent_class,
                temperature=getattr(config, "temperature", None),
                max_tokens=getattr(config, "max_tokens", None),
            )
        )
    return result
