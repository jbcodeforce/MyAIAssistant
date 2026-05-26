"""Parse customer index-style markdown using Agno (replaces agent_core NoteParserAgent)."""

from __future__ import annotations

import json
import re

from agno.agent import Agent

from ai_assist_cli.agents.note_parse_models import (
    MeetingExtract,
    NoteParseResult,
    NoteParserExtraction,
    OrganizationExtract,
    PersonExtract,
    ProjectExtract,
    StepExtract,
)
from ai_assist_cli.services.llm_model import build_openai_like_model

NOTE_PARSER_INSTRUCTIONS = """You extract structured data from a customer engagement markdown note (e.g. index.md).

Typical structure:
- Title / H1 often holds the organization name.
- Sections such as Team, People, Stakeholders list persons (roles optional).
- Context, Products, Technology describe the org or project.
- Past steps and Next steps are bullets or numbered lists with actions and optionally owners.
- Meeting sections (Discovery, Weekly sync, etc.) become meetings with title and full section body as content.

Return structured output matching the schema. Use empty lists and nulls where unknown.
Do not invent organizations or meetings not grounded in the markdown."""

_JSON_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.DOTALL)


def _extract_json(text: str) -> str:
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    text = text.strip()
    m = _JSON_BLOCK.search(text)
    if m:
        return m.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


def _parse_organization(raw: object) -> OrganizationExtract | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return OrganizationExtract(**raw)
    if isinstance(raw, str):
        return OrganizationExtract(name=raw, description=None)
    return None


def _parse_persons(raw: object) -> list[PersonExtract]:
    if not isinstance(raw, list):
        return []
    out: list[PersonExtract] = []
    for p in raw:
        if isinstance(p, dict):
            out.append(PersonExtract(**p))
        elif isinstance(p, str):
            out.append(PersonExtract(name=p, role=None, context=None))
    return out


def _parse_project(raw: object) -> ProjectExtract | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        return ProjectExtract(name=raw, description=None, past_steps=[], next_steps=[])
    if not isinstance(raw, dict):
        return None
    past = [
        StepExtract(**s) if isinstance(s, dict) else StepExtract(what=str(s), who="to_be_decided")
        for s in raw.get("past_steps", [])
    ]
    nxt = [
        StepExtract(**s) if isinstance(s, dict) else StepExtract(what=str(s), who="to_be_decided")
        for s in raw.get("next_steps", [])
    ]
    return ProjectExtract(
        name=raw.get("name"),
        description=raw.get("description"),
        past_steps=past,
        next_steps=nxt,
    )


def _parse_meetings(raw: object) -> list[MeetingExtract]:
    if not isinstance(raw, list):
        return []
    return [
        MeetingExtract(**m)
        for m in raw
        if isinstance(m, dict) and "title" in m and "content" in m
    ]


def _dict_to_result(data: dict) -> NoteParseResult:
    return NoteParseResult(
        organization=_parse_organization(data.get("organization")),
        persons=_parse_persons(data.get("persons", [])),
        project=_parse_project(data.get("project")),
        meetings=_parse_meetings(data.get("meetings", [])),
        parse_error=None,
    )


def _parse_note_output(raw: object) -> NoteParseResult:
    """Normalize Agno run output to NoteParseResult."""
    if isinstance(raw, NoteParseResult):
        return raw
    if isinstance(raw, NoteParserExtraction):
        return NoteParseResult(
            organization=raw.organization,
            persons=raw.persons,
            project=raw.project,
            meetings=raw.meetings,
            parse_error=None,
        )
    if hasattr(raw, "model_dump"):
        try:
            return _dict_to_result(raw.model_dump())
        except Exception:
            pass
    if isinstance(raw, dict):
        return _dict_to_result(raw)
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return _dict_to_result(data)
        except json.JSONDecodeError:
            pass
        try:
            blob = _extract_json(raw)
            data = json.loads(blob)
            if isinstance(data, dict):
                return _dict_to_result(data)
        except (json.JSONDecodeError, ValueError):
            pass
    return NoteParseResult(
        parse_error=f"Could not parse extraction output: {type(raw).__name__}",
    )


def build_note_parser_agent() -> Agent:
    """Single-turn extraction agent with structured output."""
    return Agent(
        name="NoteParser",
        model=build_openai_like_model(),
        instructions=NOTE_PARSER_INSTRUCTIONS,
        markdown=True,
        output_schema=NoteParserExtraction,
        structured_outputs=True,
    )


async def parse_customer_note(content: str) -> NoteParseResult:
    """Run LLM extraction on full markdown; returns structured fields or parse_error."""
    agent = build_note_parser_agent()
    run = await agent.arun(content)
    return _parse_note_output(run.content)
