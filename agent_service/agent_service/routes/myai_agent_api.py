import logging
from agent_service.agents.agent_factory import get_or_create_agent_factory, AgentConfigReference
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/myai", tags=["myai"])



@router.get("/agents", response_model=list[AgentConfigReference])
async def get_agent_names():
    try:
        factory = get_or_create_agent_factory() 
        return factory.get_agent_references()
    except Exception as e:
        logger.exception("Failed to get agent names")
        raise HTTPException(status_code=500, detail=str(e))