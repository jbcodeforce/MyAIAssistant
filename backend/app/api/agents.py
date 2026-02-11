import logging
import re
import yaml
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings, resolve_agent_config_dir
from app.api.schemas.agent import AgentConfigResponse, AgentDetailResponse, SavePromptRequest
from agent_core.agents.agent_factory import get_agent_factory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Safe agent name: alphanumeric and underscore only (no path traversal)
AGENT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _get_factory():
    settings = get_settings()
    config_dir = resolve_agent_config_dir(settings.agent_config_dir)
    return get_agent_factory(config_dir=config_dir)


@router.get("/", response_model=list[AgentConfigResponse])
async def list_agents():
    """
    List configured agents (read-only). Data comes from the agent config directory, no database.
    """
    try:
        factory = _get_factory()
    except Exception as e:
        logger.exception("Failed to get agent factory")
        raise HTTPException(status_code=503, detail="Agent configuration unavailable") from e

    result = []
    for name in factory.list_agents():
        config = factory.get_config(name)
        if config is None:
            continue
        base_url = getattr(config, "base_url", None) or (config.get_base_url() if hasattr(config, "get_base_url") else None)
        result.append(
            AgentConfigResponse(
                name=config.name,
                description=config.description or "",
                model=config.model,
                agent_class=config.agent_class,
                temperature=getattr(config, "temperature", None),
                max_tokens=getattr(config, "max_tokens", None),
                base_url=base_url,
            )
        )
    return result


@router.get("/{name}", response_model=AgentDetailResponse)
async def get_agent(name: str):
    """
    Get one agent's full detail including sys_prompt for editing.
    """
    try:
        factory = _get_factory()
    except Exception as e:
        logger.exception("Failed to get agent factory")
        raise HTTPException(status_code=503, detail="Agent configuration unavailable") from e

    config = factory.get_config(name)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {name}")

    base_url = getattr(config, "base_url", None) or (config.get_base_url() if hasattr(config, "get_base_url") else None)
    sys_prompt = getattr(config, "sys_prompt", None) or ""

    return AgentDetailResponse(
        name=config.name,
        description=config.description or "",
        model=config.model,
        agent_class=config.agent_class,
        temperature=getattr(config, "temperature", None),
        max_tokens=getattr(config, "max_tokens", None),
        base_url=base_url,
        sys_prompt=sys_prompt,
    )


@router.put("/{name}/prompt")
async def save_agent_prompt(name: str, body: SavePromptRequest):
    """
    Save the agent's prompt to the workspace agents folder (resolved agent config directory).
    Writes prompt.md and creates agent.yaml from current config if missing, so agent_core loads the override.
    """
    if not AGENT_NAME_PATTERN.match(name):
        raise HTTPException(status_code=400, detail="Invalid agent name")

    try:
        factory = _get_factory()
    except Exception as e:
        logger.exception("Failed to get agent factory")
        raise HTTPException(status_code=503, detail="Agent configuration unavailable") from e

    config = factory.get_config(name)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Agent not found: {name}")

    settings = get_settings()
    config_dir = Path(resolve_agent_config_dir(settings.agent_config_dir))

    if "agent_core" in config_dir.parts:
        raise HTTPException(
            status_code=400,
            detail="Cannot save to agent_core package path; set agent_config_dir to a workspace folder (e.g. config)",
        )

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
