import logging
from agent_service.agents.agent_factory import get_or_create_agent_factory, AgentConfigReference
from fastapi import APIRouter, HTTPException
import yaml
import re
from agent_service.agents.model import SavePromptRequest
from pathlib import Path

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




AGENT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")

@router.put("/agents/{name}/prompt")
async def save_agent_prompt(name: str, body: SavePromptRequest):
    """
    Save the agent's prompt to the workspace agents folder (resolved agent config directory).
    Writes prompt.md and creates agent.yaml from current config if missing, so agent_core loads the override.
    """
    if not AGENT_NAME_PATTERN.match(name):
        raise HTTPException(status_code=400, detail="Invalid agent name")

    try:
        factory = get_or_create_agent_factory() 
    except Exception as e:
        logger.exception("Failed to get agent factory")
        raise HTTPException(status_code=503, detail="Agent configuration unavailable") from e

    agent_config = factory.get_ai_agent(name)
    if agent_config is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {name}")

    config_dir = Path(f"./agents/{name}/")
    if not config_dir.exists():
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.exception("Failed to create config directory")
            raise HTTPException(status_code=503, detail=f"Workspace agents folder is not writable: {e}") from e

    agent_dir = config_dir / name
    try:
        agent_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.exception("Failed to create agent directory")
        raise HTTPException(status_code=503, detail=f"Workspace agents folder is not writable: {e}") from e

    prompt_path = agent_dir / "prompt.md"
    try:
        prompt_path.write_text(body.prompt, encoding="utf-8")
    except OSError as e:
        logger.exception("Failed to write prompt.md")
        raise HTTPException(status_code=503, detail=f"Failed to save prompt: {e}") from e

    yaml_path = agent_dir / "agent.yaml"
    if not yaml_path.exists():
        base_url = getattr(config, "base_url", None) or (config.get_base_url() if hasattr(config, "get_base_url") else None)
        data = {
            "name": config.name,
            "description": config.description or "A general purpose agent.",
            "temperature": getattr(config, "temperature", 0.7),
            "max_tokens": getattr(config, "max_tokens", 10000),
            "class": config.agent_class or "agent_core.agents.base_agent.BaseAgent",
            "model": config.model or "gpt-4o-mini",
        }
        if base_url:
            data["base_url"] = base_url
        if getattr(config, "use_rag", False):
            data["use_rag"] = True
            data["rag_top_k"] = getattr(config, "rag_top_k", 3)
        try:
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except OSError as e:
            logger.exception("Failed to write agent.yaml")
            raise HTTPException(status_code=503, detail=f"Failed to create agent config: {e}") from e

    return {"status": "ok", "message": "Prompt saved"}
