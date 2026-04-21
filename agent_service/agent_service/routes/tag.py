"""Task tagging compatibility route for backend proxy."""

import json
import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent_service.agents.chat import _build_model
from agno.agent import Agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tag", tags=["tag"])

_tag_agent: Agent | None = None


def _get_tag_agent() -> Agent:
    global _tag_agent
    if _tag_agent is None:
        _tag_agent = Agent(
            name="Tag",
            model=_build_model(),
            instructions="""You suggest tags for a task based on its title and description. Reply with a single JSON object only:
{"message": "brief explanation", "tags": ["tag1", "tag2", ...]}
Use lowercase, short tags (e.g. bug, feature, docs, urgent). Return 1-5 tags.""",
        )
    return _tag_agent


class TagTaskRequest(BaseModel):
    task_title: str = Field(..., min_length=1)
    task_description: str | None = Field(None)


def _extract_json(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


@router.post("/task")
async def tag_task(req: TagTaskRequest) -> dict[str, Any]:
    """Suggest tags for a task. Backend applies them to the todo."""
    try:
        agent = _get_tag_agent()
    except Exception as e:
        logger.exception("Chat agent not available")
        raise HTTPException(status_code=503, detail=str(e))
    user_msg = f"Title: {req.task_title}\nDescription: {req.task_description or ''}"
    try:
        run = await agent.arun(user_msg)
        raw = run.content if hasattr(run, "content") else str(run)
    except Exception as e:
        logger.exception("Tag run failed")
        raise HTTPException(status_code=500, detail=str(e))
    try:
        json_str = _extract_json(raw)
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return {"message": raw[:500] if raw else "No response", "tags": []}
    tags = data.get("tags", [])
    if not isinstance(tags, list):
        tags = [str(tags)] if tags else []
    return {
        "message": data.get("message", ""),
        "tags": [str(t).strip().lower() for t in tags if str(t).strip()],
    }
