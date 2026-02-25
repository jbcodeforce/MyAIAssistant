"""Integration tests for agent routing: 
1. Classify query to determine intent
2. Route query to appropriate agent
3. Execute agent and return response
"""

import pytest
import json
from pathlib import Path
from agent_core.agents.base_agent import AgentInput, AgentResponse
from agent_core.agents.agent_factory import get_agent_factory
from .conftest import (
    requires_local_server,
    requires_local_model
)

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

@pytest.mark.integration
class TestOpenAIAgents:
    @pytest.fixture
    def factory(self):
        """Create factory pointing to real config directory."""
        factory = get_agent_factory(config_dir=config_dir)
        return factory


    @pytest.mark.asyncio
    async def test_deep_thinker_agent(self, factory):
        """Test deep thinker agent."""
        agent = factory.create_agent("DeepThinker")
        query = "what to address to reduce carbon footprint for water waste processing"
        response = await agent.execute(AgentInput(query=query)) 
        print(f"\n----\n{json.dumps(response.__dict__, indent=2, default=str)}\n----\n")
        assert response.message is not None
        assert response.context_used is not None
        assert response.agent_type == "DeepThinker"
      

   