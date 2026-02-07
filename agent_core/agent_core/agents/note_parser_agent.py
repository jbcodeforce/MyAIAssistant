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

        Returns:
            Tuple of (parsed data dict or None, error message or None)
        """
        try:
            json_text = self._extract_json(response_text)
            data = json.loads(json_text)
            organization = None
            if data.get("organization"):
                organization = OrganizationExtract(**data["organization"])
            persons = [
                PersonExtract(**p) for p in data.get("persons", [])
            ]
            project = None
            if data.get("project"):
                proj = data["project"]
                project = ProjectExtract(
                    name=proj.get("name"),
                    description=proj.get("description"),
                    past_steps=[StepExtract(**s) for s in proj.get("past_steps", [])],
                    next_steps=[StepExtract(**s) for s in proj.get("next_steps", [])],
                )
            meetings = [
                MeetingExtract(**m) for m in data.get("meetings", [])
            ]
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
