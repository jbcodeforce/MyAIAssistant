"""Integration tests for agent routing: 
1. Classify query to determine intent
2. Route query to appropriate agent
3. Execute agent and return response
"""

import pytest
import json
from pathlib import Path
from agent_core.agents.agent_config import AgentConfig
from agent_core.agents.base_agent import AgentInput, AgentResponse
from agent_core.agents.mlx_base_agent import MLXBaseAgent

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

@pytest.mark.integration
class TestOpenAIAgents:
    @pytest.fixture
    def agent(self):
        """Create factory pointing to real config directory."""
        config = AgentConfig(model="mlx-community/Qwen3-4B-Instruct-2507-4bit")
        config.sys_prompt = config.sys_prompt or "You are a helpful assistant."
        agent = MLXBaseAgent(config=config)
        return agent



    @pytest.mark.asyncio
    async def test_deep_thinker_agent(self, agent):
        """Test deep thinker agent."""
        response = await agent.execute(AgentInput(query="what to address to reduce carbon footprint for water waste processing")) 
        print(f"\n----\n{json.dumps(response.__dict__, indent=2, default=str)}\n----\n")
        assert response.message is not None
        assert response.context_used is not None
        assert response.agent_type == "DeepThinker"
      

   