"""Integration tests for MeetingAgent with Ollama backend.

These tests require a running Ollama server with the specified model available.

Run with: pytest tests/it/test_meeting_agent.py -v -m integration
"""

import pytest
from pathlib import Path
import json
from agent_core.agents.agent_factory import get_agent_factory
from agent_core.agents.base_agent import AgentInput, AgentResponse

from .conftest import requires_ollama, requires_model


@pytest.mark.integration
@requires_ollama
@requires_model
class TestPersonaAgent:
    """Given a problem the agent builds a persona based on the problem."""

    @pytest.fixture
    def factory(self):
        """Create factory pointing to real config directory."""
        return get_agent_factory()

    @pytest.mark.asyncio
    async def test_simple_persona_building(self, factory):
        """Test extracting information from a simple meeting note."""
        agent = factory.create_agent("PersonaAgent")
        problem = "I need to create knowledge base for environment engineering curriculum."
        
        result = await agent.execute(AgentInput(query=problem))
        
        # Verify response type and basic fields
        assert isinstance(result, AgentResponse)
        print(json.dumps(result.__dict__, indent=2, default=str))   

