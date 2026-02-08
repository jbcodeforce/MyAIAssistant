"""Integration tests for MeetingAgent with Ollama backend.

These tests require a running Ollama server with the specified model available.

Run with: pytest tests/it/test_meeting_agent.py -v -m integration
"""

import pytest
from pathlib import Path
from agent_core.agents.meeting_agent import MeetingAgentResponse
from agent_core.agents.agent_factory import get_agent_factory, AgentFactory
from agent_core.agents.base_agent import AgentInput

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

from .conftest import requires_local_server, requires_local_model

@pytest.fixture
def factory() -> AgentFactory:
    """Create a QueryClassifier with Ollama config."""
    factory = get_agent_factory()
    return factory

@pytest.mark.integration
@requires_local_server
@requires_local_model
@pytest.mark.asyncio
class TestMeetingAgent:
    """Tests for the MeetingAgent class."""

    @pytest.mark.asyncio
    async def test_simple_meeting_note(self, factory):
        """Test extracting information from a simple meeting note."""
        agent = factory.create_agent("MeetingAgent")
        meeting_note = """
## Meeting 01/07
* Will Chen, Christian Dupont, Neil Radisson
* Issue with ARRAY_AGG function. In Java the Array_agg ROW seems to work
* Less degraded statement alert reported since beginning of the year.
        """
        
        result = await agent.execute(AgentInput(query=meeting_note))
        
        # Verify response type and basic fields
        assert isinstance(result, MeetingAgentResponse)
        assert len(result.cleaned_notes) > 0
        print(f"Cleaned notes:\n{result.cleaned_notes}")
        
        # Verify parsing succeeded
        assert result.parse_error is None, f"Parse error: {result.parse_error}"
        
        # Verify persons were extracted
        attendees = result.attendees
        assert len(attendees) == 3, f"Expected 3 attendees, got {len(attendees)}"
        attendee_names = [a.name for a in attendees]
        print(f"Attendees: {attendee_names}")
        assert "Will Chen" in attendee_names or "Chen" in str(attendee_names)
        assert "Christian Dupont" in attendee_names or "Dupont" in str(attendee_names)
        assert "Neil Radisson" in attendee_names or "Radisson" in str(attendee_names)
        
        # Verify next steps were extracted (at least one)
        next_steps = result.next_steps
        assert len(next_steps) >= 1, f"Expected at least 1 next step, got {len(next_steps)}"
        print(f"Next steps: {[(ns.what, ns.who) for ns in next_steps]}")
        
        # Verify key points were extracted (at least one)
        key_points = result.key_points
        assert len(key_points) >= 1, f"Expected at least 1 key point, got {len(key_points)}"
        print(f"Key points: {[kp.point for kp in key_points]}")
        
        # Verify metadata
        assert result.metadata.get("parsed_successfully") is True


    @pytest.mark.asyncio
    async def test_meeting_note_with_context(self, factory):
        """Test extracting information from a simple meeting note with context."""
        agent = factory.create_agent("MeetingAgent")
        meeting_note = """
## Meeting 01/07
* Will Chen, Christian Dupont, Neil Radisson
* The debezium connector needs to create the topic and the schema.
* How to manage schema evolution?
* how to process the debezium envelop.
        """
        context = """
        {"organization": "JJJJJ is looking to move to reduce their batch processing to get close to real-time data, and develop a data as a product practices",
       "project": "realtime data processing from their AWS RDS, to Iceberg tables."
       }
       """
        result = await agent.execute(AgentInput(query=meeting_note, context={"context": context}))
        assert isinstance(result, MeetingAgentResponse)
        assert len(result.cleaned_notes) > 0
        print(f"Cleaned notes:\n{result.cleaned_notes}")
        assert result.parse_error is None, f"Parse error: {result.parse_error}"
        assert len(result.attendees) == 3, f"Expected 3 attendees, got {len(result.attendees)}"
        next_steps = result.next_steps
        assert len(next_steps) >= 1, f"Expected at least 1 next step, got {len(next_steps)}"
        print(f"Next steps: {[(ns.what, ns.who) for ns in next_steps]}")
        key_points = result.key_points
        assert len(key_points) >= 1, f"Expected at least 1 key point, got {len(key_points)}"
        print(f"Key points: {[kp.point for kp in key_points]}")
        key_points = result.key_points
        assert len(key_points) >= 1, f"Expected at least 1 key point, got {len(key_points)}"
        print(f"Key points: {[kp.point for kp in key_points]}")