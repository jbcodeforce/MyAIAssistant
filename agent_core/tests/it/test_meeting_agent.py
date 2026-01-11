"""Integration tests for MeetingAgent with Ollama backend.

These tests require a running Ollama server with the specified model available.

Run with: pytest tests/it/test_meeting_agent.py -v -m integration
"""

import pytest

from agent_core.agents.meeting_agent import MeetingAgentResponse, MeetingOutput
from agent_core.agents.factory import AgentFactory

from .conftest import requires_ollama, requires_model


@pytest.mark.integration
@requires_ollama
@requires_model
class TestMeetingAgent:
    """Given a meeting note the agent extracts the key points, persons present, and builds next steps."""

    @pytest.fixture
    def factory(self):
        """Create factory pointing to real config directory."""
        return AgentFactory()

    @pytest.mark.asyncio
    async def test_simple_meeting_note(self, factory):
        """Test extracting information from a simple meeting note."""
        agent = factory.create_agent("MeetingAgent")
        meeting_note = """
## Meeting 01/07
* Presents: Will Chen, Christian Dupont, Neil Radisson
* Issue with ARRAY_AGG function. In Java the Array_agg ROW seems to work
* Less degraded statement alert reported since beginning of the year.
        """
        
        result = await agent.execute(query=meeting_note)
        
        # Verify response type and basic fields
        assert isinstance(result, MeetingAgentResponse)
        assert result.agent_type == "meeting"
        assert len(result.message) > 0
        print(f"Raw message:\n{result.message}")
        
        # Verify parsing succeeded
        assert result.parse_error is None, f"Parse error: {result.parse_error}"
        assert result.meeting_output is not None
        assert isinstance(result.meeting_output, MeetingOutput)
        
        # Verify persons were extracted
        persons = result.meeting_output.persons
        assert len(persons) == 3, f"Expected 3 persons, got {len(persons)}"
        person_names = [p.name for p in persons]
        print(f"Persons: {person_names}")
        assert "Will Chen" in person_names or "Chen" in str(person_names)
        assert "Christian Dupont" in person_names or "Dupont" in str(person_names)
        assert "Neil Radisson" in person_names or "Radisson" in str(person_names)
        
        # Verify next steps were extracted (at least one)
        next_steps = result.meeting_output.next_steps
        assert len(next_steps) >= 1, f"Expected at least 1 next step, got {len(next_steps)}"
        print(f"Next steps: {[(ns.what, ns.who) for ns in next_steps]}")
        
        # Verify key points were extracted (at least one)
        key_points = result.meeting_output.key_points
        assert len(key_points) >= 1, f"Expected at least 1 key point, got {len(key_points)}"
        print(f"Key points: {[kp.point for kp in key_points]}")
        
        # Verify metadata
        assert result.metadata.get("parsed_successfully") is True
