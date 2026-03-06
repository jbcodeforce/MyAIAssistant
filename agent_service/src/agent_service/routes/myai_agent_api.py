import logging
from agent_service.agents.agent_factory import get_or_create_agent_factory
from fastapi import APIRouter, HTTPException
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/myai", tags=["myai"])

@router.get("/agents", response_model=list[str])
async def get_agent_names():
    try:
        factory = get_or_create_agent_factory() 
        return factory.get_agent_name_list()
    except Exception as e:
        logger.exception("Failed to get agent names")
        raise HTTPException(status_code=500, detail=str(e))