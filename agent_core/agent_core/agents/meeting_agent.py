"""Meeting agent for extracting structured information from meeting notes."""

import json
import logging
import re
from typing import Optional

from pydantic import BaseModel, Field

from agent_core.agents.base_agent import BaseAgent, AgentResponse

logger = logging.getLogger(__name__)


class Person(BaseModel):
    """A person present at the meeting."""
    name: str
    last_met_date: Optional[str] = None


class NextStep(BaseModel):
    """An actionable next step from the meeting."""
    what: str
    who: str = "to_be_decided"


class KeyPoint(BaseModel):
    """A key discussion point from the meeting."""
    point: str

class MeetingAgentResponse(AgentResponse):
    """Extended response from MeetingAgent with structured meeting data."""
    attendees: list[Person] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)
    key_points: list[KeyPoint] = Field(default_factory=list)
    cleaned_notes: str = Field(..., description="Cleaned meeting notes")
    parse_error: Optional[str] = None


class MeetingAgent(BaseAgent):
    """
    Agent specialized in working with meeting notes.
    
    Extracts persons present, key discussion points, and actionable next steps
    from meeting notes and returns structured data.
    """
    
    agent_type = "meeting"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def execute(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None
    ) -> MeetingAgentResponse:
        """
        Execute meeting note extraction.
        
        Args:
            query: The meeting notes text
            conversation_history: Previous messages in conversation
            context: Additional context (may be extract of project description, or organization description.)
            
        Returns:
            MeetingAgentResponse with structured meeting data
        """
        context = context or "No additional context provided"  # TODO assess when it will be needed
        
        # Build messages with query substitution in prompt
        system_prompt = self.build_system_prompt({"context": context})
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        messages.append({"role": "user", "content": query})
        
        # Generate response from LLM
        response_text = await self._call_llm(messages)
        
        # Parse the JSON response
        parsed_data, parse_error = self._parse_meeting_output(response_text)
        
        # Build response with parsed data or defaults if parsing failed
        if parsed_data:
            return MeetingAgentResponse(
                message=response_text,
                attendees=parsed_data["attendees"],
                next_steps=parsed_data["next_steps"],
                key_points=parsed_data["key_points"],
                cleaned_notes=parsed_data["cleaned_notes"],
                parse_error=None,
                model=self.model,
                provider=self.provider,
                agent_type=self.agent_type,
                metadata={
                    "parsed_successfully": True
                }
            )
        else:
            return MeetingAgentResponse(
                message=response_text,
                attendees=[],
                next_steps=[],
                key_points=[],
                cleaned_notes=response_text,  # Use raw response as fallback
                parse_error=parse_error,
                model=self.model,
                provider=self.provider,
                agent_type=self.agent_type,
                metadata={
                    "parsed_successfully": False
                }
            )
    
    def _parse_meeting_output(self, response_text: str) -> tuple[Optional[dict], Optional[str]]:
        """
        Parse the LLM response into structured meeting data.
        
        Args:
            response_text: Raw text response from LLM
            
        Returns:
            Tuple of (parsed data dict or None, error message or None)
        """
        try:
            # Try to extract JSON from the response
            json_text = self._extract_json(response_text)
            data = json.loads(json_text)
            
            # Parse into Pydantic models
            attendees = [Person(**p) for p in data.get("attendees", [])]
            next_steps = [NextStep(**ns) for ns in data.get("next_steps", [])]
            key_points = [KeyPoint(**kp) if isinstance(kp, dict) else KeyPoint(point=str(kp)) 
                         for kp in data.get("key_points", [])]
            
            return {
                "attendees": attendees,
                "next_steps": next_steps,
                "key_points": key_points,
                "cleaned_notes": data.get("cleaned_notes", "")
            }, None
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from LLM response: {e}")
            return None, f"JSON parse error: {str(e)}"
        except Exception as e:
            logger.warning(f"Failed to parse meeting output: {e}")
            return None, f"Parse error: {str(e)}"
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text, handling markdown code blocks and cleaning invalid syntax.
        
        Args:
            text: Text potentially containing JSON
            
        Returns:
            Extracted JSON string
        """
        # Remove markdown code block if present
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            json_text = json_match.group(1).strip()
        else:
            # Try to find JSON object directly
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_text = text[start:end + 1]
            else:
                json_text = text.strip()
        
        # Remove JavaScript-style comments (// ...) that LLMs sometimes add
        json_text = re.sub(r'//[^\n]*', '', json_text)
        
        # Remove trailing commas before ] or } (common LLM error)
        json_text = re.sub(r',\s*([\]}])', r'\1', json_text)
        
        return json_text