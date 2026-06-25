import logging
import os
from pathlib import Path

from agent_service.agents.agent_factory import get_or_create_agent_factory, AgentConfigReference
from fastapi import APIRouter, HTTPException
import yaml
import re
from agent_service.agents.model import SavePromptRequest

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


def _workspace_agents_dir(name: str) -> Path:
    base = os.getenv("AGENT_CONFIG_DIR", "agent_service/agents/config")
    return Path(base) / name


@router.put("/agents/{name}/prompt")
async def save_agent_prompt(name: str, body: SavePromptRequest):
    """
    Save the agent's prompt to the workspace agents folder.
    Writes prompt.md and creates agent.yaml from current config if missing.
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

    agent_dir = _workspace_agents_dir(name)
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
        base_url = getattr(agent_config, "base_url", None)
        data = {
            "name": agent_config.name,
            "description": agent_config.description or "A general purpose agent.",
            "temperature": getattr(agent_config, "temperature", 0.7),
            "max_tokens": getattr(agent_config, "max_tokens", 10000),
            "agent_class": agent_config.agent_class or "agent_service.agents.base_ai_agent.AIAgent",
            "model": agent_config.model or "gpt-4o-mini",
        }
        if base_url:
            data["llm_url"] = base_url
        if getattr(agent_config, "use_rag", False):
            data["use_rag"] = True
            data["rag_top_k"] = getattr(agent_config, "rag_top_k", 3)
        try:
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except OSError as e:
            logger.exception("Failed to write agent.yaml")
            raise HTTPException(status_code=503, detail=f"Failed to create agent config: {e}") from e

    return {"status": "ok", "message": "Prompt saved"}
