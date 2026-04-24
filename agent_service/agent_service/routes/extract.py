"""Extract meeting structured data (compatibility route for backend proxy)."""

import json
import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent_service.agents.chat import _build_model
from agent_service.tools.legacy_customer_import.extractor import extract_legacy_customer_index
from agno.agent import Agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extract", tags=["extract"])

_extract_agent: Agent | None = None


def _get_extract_agent() -> Agent:
    global _extract_agent
    if _extract_agent is None:
        _extract_agent = Agent(
            name="Extract",
            model=_build_model(),
            instructions="""You extract structured information from meeting notes. Reply with a single JSON object only, no other text.
Use this exact structure:
{
  "attendees": [{"name": "string", "last_met_date": null}],
  "next_steps": [{"what": "string", "who": "string or to_be_decided"}],
  "key_points": [{"point": "string"}],
  "cleaned_notes": "markdown string summary of the meeting"
}
Extract all mentioned people, actionable next steps with assignee (use to_be_decided if unknown), and key discussion points. cleaned_notes should be a concise formatted summary.""",
        )
    return _extract_agent


class ExtractMeetingRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Meeting note text")
    organization: str | None = Field(None, description="Organization context")
    project: str | None = Field(None, description="Project context")
    attendees: str | None = Field(None, description="Known attendees list")


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


@router.post("/meeting")
async def extract_meeting(req: ExtractMeetingRequest) -> dict[str, Any]:
    """Extract attendees, next_steps, key_points, cleaned_notes from meeting content."""
    try:
        agent = _get_extract_agent()
    except Exception as e:
        logger.exception("Chat agent not available")
        raise HTTPException(status_code=503, detail=str(e))
    user_msg = req.content
    if req.organization or req.project or req.attendees:
        user_msg = (
            "Context:\n"
            + (f"Organization: {req.organization}\n" if req.organization else "")
            + (f"Project: {req.project}\n" if req.project else "")
            + (f"Attendees: {req.attendees}\n" if req.attendees else "")
            + "\nMeeting notes:\n"
            + req.content
        )
    try:
        run = await agent.arun(user_msg)
        raw = run.content if hasattr(run, "content") else str(run)
    except Exception as e:
        logger.exception("Extract run failed")
        raise HTTPException(status_code=500, detail=str(e))
    try:
        json_str = _extract_json(raw)
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning("Extract JSON parse failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to parse extraction JSON")
    attendees = data.get("attendees", [])
    next_steps = data.get("next_steps", [])
    key_points = data.get("key_points", [])
    cleaned_notes = data.get("cleaned_notes", "")
    return {
        "attendees": [
            {"name": a.get("name", str(a)) if isinstance(a, dict) else str(a), "last_met_date": a.get("last_met_date") if isinstance(a, dict) else None}
            for a in attendees
        ],
        "next_steps": [
            {"what": ns.get("what", str(ns)), "who": ns.get("who", "to_be_decided") if isinstance(ns, dict) else "to_be_decided"}
            for ns in next_steps
        ],
        "key_points": [{"point": kp.get("point", str(kp)) if isinstance(kp, dict) else str(kp)} for kp in key_points],
        "cleaned_notes": cleaned_notes,
    }


class ExtractCustomerIndexRequest(BaseModel):
    """Full legacy customer engagement note markdown."""

    content: str = Field(..., min_length=1, description="Legacy index.md or engagement note markdown")
    folder_slug: str | None = Field(None, description="Account folder slug hint for naming")


@router.post("/customer-index")
async def extract_customer_index(req: ExtractCustomerIndexRequest) -> dict[str, Any]:
    """Extract organization, project, and meetings from a legacy customer note (JSON only; no persistence)."""
    try:
        data = extract_legacy_customer_index(req.content, folder_slug=req.folder_slug)
    except Exception as e:
        logger.exception("Legacy customer index extraction failed")
        raise HTTPException(status_code=500, detail=str(e))
    return data.model_dump(mode="json")
