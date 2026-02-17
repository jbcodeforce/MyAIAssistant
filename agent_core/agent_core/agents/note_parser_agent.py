"""Index parser agent for extracting structured data from customer note markdown."""

import json
import logging
import re
from typing import Optional

from pydantic import BaseModel, Field

from agent_core.agents.base_agent import BaseAgent, AgentResponse, AgentInput

logger = logging.getLogger(__name__)


class OrganizationExtract(BaseModel):
    """Extracted organization from customer note."""
    name: str
    description: Optional[str] = None


class PersonExtract(BaseModel):
    """Extracted person from customer note."""
    name: str
    role: Optional[str] = None
    context: Optional[str] = None


class StepExtract(BaseModel):
    """A step with action and assignee."""
    what: str
    who: str = "to_be_decided"


class ProjectExtract(BaseModel):
    """Extracted project from customer note."""
    name: Optional[str] = None
    description: Optional[str] = None
    past_steps: list[StepExtract] = Field(default_factory=list)
    next_steps: list[StepExtract] = Field(default_factory=list)


class MeetingExtract(BaseModel):
    """Extracted meeting section from customer note."""
    title: str
    content: str


class NoteParserExtraction(BaseModel):
    """Root structure for LLM extraction output; aligns prompt and parsing."""

    organization: Optional[OrganizationExtract] = None
    persons: list[PersonExtract] = Field(default_factory=list)
    project: Optional[ProjectExtract] = None
    meetings: list[MeetingExtract] = Field(default_factory=list)


class NoteParserResponse(AgentResponse):
    """Extended response from IndexParserAgent with structured extraction data."""
    organization: Optional[OrganizationExtract] = None
    persons: list[PersonExtract] = Field(default_factory=list)
    project: Optional[ProjectExtract] = None
    meetings: list[MeetingExtract] = Field(default_factory=list)
    parse_error: Optional[str] = None


class NoteParserAgent(BaseAgent):
    """
    Agent that parses customer note markdown (e.g. index.md) and extracts
    organization, persons, project, and meeting sections as structured JSON.
    """

    agent_type = "note_parser"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """Build system prompt with base template plus expected JSON schema."""
        base = super().build_system_prompt(context)
        schema = NoteParserExtraction.model_json_schema()
        schema_block = (
            "\n\n### Expected JSON schema\n\n"
            "Respond with a JSON object that conforms to this schema:\n\n"
            "```json\n"
            f"{json.dumps(schema, indent=2)}\n"
            "```\n\n"
            "Respond ONLY with the JSON object, no additional text or markdown."
        )
        return base + schema_block

    async def execute(self, input_data: AgentInput) -> NoteParserResponse:
        """
        Execute note extraction.

        Args:
            input_data: AgentInput with query = full markdown content

        Returns:
           NoteParserResponse with organization, persons, project, meetings
        """
        messages, context_used, _ = await self._build_messages(input_data)
        logger.info("NoteParserAgent executing with %d messages", len(messages))
        response = await self._llm_client.chat_async(
            messages=messages, config=self._config
        )
        response_text = response.content
        logger.info("NoteParserAgent raw response length: %d", len(response_text))
        parsed_data, parse_error = self._parse_output(response_text)
        if parsed_data:
            return NoteParserResponse(
                message=response_text,
                organization=parsed_data.get("organization"),
                persons=parsed_data.get("persons", []),
                project=parsed_data.get("project"),
                meetings=parsed_data.get("meetings", []),
                parse_error=None,
                agent_type=self.agent_type,
                context_used=context_used,
                metadata={"parsed_successfully": True},
            )
        return NoteParserResponse(
            message=response_text,
            organization=None,
            persons=[],
            project=None,
            meetings=[],
            parse_error=parse_error,
            agent_type=self.agent_type,
            context_used=context_used,
            metadata={"parsed_successfully": False},
        )

    def _parse_output(self, response_text: str) -> tuple[Optional[dict], Optional[str]]:
        """
        Parse the LLM response into structured extraction data.

        Tolerates LLM returning primitives (e.g. organization as a string);
        only unpacks dicts for Pydantic models.
        """
        try:
            json_text = self._extract_json(response_text)
            data = json.loads(json_text)
            organization = self._parse_organization(data.get("organization"))
            persons = self._parse_persons(data.get("persons", []))
            project = self._parse_project(data.get("project"))
            meetings = self._parse_meetings(data.get("meetings", []))
            return {
                "organization": organization,
                "persons": persons,
                "project": project,
                "meetings": meetings,
            }, None
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON from IndexParserAgent response: %s", e)
            return None, f"JSON parse error: {str(e)}"
        except Exception as e:
            logger.warning("Failed to parse index parser output: %s", e)
            return None, f"Parse error: {str(e)}"

    def _parse_organization(self, raw: Optional[object]) -> Optional[OrganizationExtract]:
        """Parse organization; raw may be a dict or a string (name only)."""
        if raw is None:
            return None
        if isinstance(raw, dict):
            return OrganizationExtract(**raw)
        if isinstance(raw, str):
            return OrganizationExtract(name=raw, description=None)
        return None

    def _parse_persons(self, raw: object) -> list[PersonExtract]:
        """Parse persons list; items may be dicts or strings (name only)."""
        if not isinstance(raw, list):
            return []
        result = []
        for p in raw:
            if isinstance(p, dict):
                result.append(PersonExtract(**p))
            elif isinstance(p, str):
                result.append(PersonExtract(name=p, role=None, context=None))
        return result

    def _parse_project(self, raw: Optional[object]) -> Optional[ProjectExtract]:
        """Parse project; raw may be a dict or a string (name only)."""
        if raw is None:
            return None
        if isinstance(raw, str):
            return ProjectExtract(name=raw, description=None, past_steps=[], next_steps=[])
        if not isinstance(raw, dict):
            return None
        proj = raw
        past = [
            StepExtract(**s) if isinstance(s, dict) else StepExtract(what=str(s), who="to_be_decided")
            for s in proj.get("past_steps", [])
        ]
        next_st = [
            StepExtract(**s) if isinstance(s, dict) else StepExtract(what=str(s), who="to_be_decided")
            for s in proj.get("next_steps", [])
        ]
        return ProjectExtract(
            name=proj.get("name"),
            description=proj.get("description"),
            past_steps=past,
            next_steps=next_st,
        )

    def _parse_meetings(self, raw: object) -> list[MeetingExtract]:
        """Parse meetings list; items must be dicts with title and content."""
        if not isinstance(raw, list):
            return []
        return [
            MeetingExtract(**m) for m in raw
            if isinstance(m, dict) and "title" in m and "content" in m
        ]

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks and invalid syntax."""
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            json_text = json_match.group(1).strip()
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_text = text[start : end + 1]
            else:
                json_text = text.strip()
        json_text = re.sub(r"//[^\n]*", "", json_text)
        json_text = re.sub(r",\s*([\]}])", r"\1", json_text)
        return json_text
