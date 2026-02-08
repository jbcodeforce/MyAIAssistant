"""Integration tests for TaskAgent with real LLM calls.

These tests require a running LLM server with the specified model available.

Run with: pytest tests/it/test_task_agent.py -v -m integration
"""

import pytest
import json
from pathlib import Path
from agent_core.agents.base_agent import AgentResponse
from agent_core.agents.agent_factory import get_agent_factory
from agent_core.agents.base_agent import AgentInput

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

from .conftest import requires_local_server, requires_local_model


@pytest.mark.integration
@requires_local_server
@requires_local_model
class TestTaskAgent:
    """Given a meeting note the agent extracts the key points, persons present, and builds next steps."""

    @pytest.fixture
    def factory(self):
        """Create factory pointing to real config directory."""
        factory = get_agent_factory(config_dir=config_dir)
        return factory

    @pytest.mark.asyncio
    async def test_simple_task_decomposition(self, factory):
        """Test extracting information from a simple meeting note."""
        agent = factory.create_agent("TaskAgent")
        user_prompt = """
        help me on this task
        """
        context = {"task_title": "research environment content", "task_description": "search to build an environment engineering curriculum"}
        response = await agent.execute(AgentInput(query=user_prompt, context=context))
        
        # Verify response type and basic fields
        assert isinstance(response, AgentResponse)
        print(f"\n----\n{json.dumps(response.__dict__, indent=2, default=str)}\n----\n")
        
  