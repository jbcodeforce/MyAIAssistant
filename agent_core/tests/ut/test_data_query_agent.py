"""Tests for DataQueryAgent."""

import pytest

from agent_core.agents.base_agent import AgentInput
from agent_core.agents.data_query_agent import DataQueryAgent
from agent_core.agents.agent_config import AgentConfig


class TestDataQueryAgent:
    """Tests for DataQueryAgent."""

    @pytest.mark.asyncio
    async def test_execute_without_provider_returns_friendly_message(self):
        """When context has no data_query_provider, agent returns a friendly message."""
        config = AgentConfig(name="DataQueryAgent", model="test")
        agent = DataQueryAgent(config=config)
        input_data = AgentInput(query="List my tasks from last month", context={})
        response = await agent.execute(input_data)
        assert response is not None
        assert response.message
        assert "cannot query" in response.message.lower() or "dashboard" in response.message.lower()
        assert response.agent_type in ("data_query", "DataQueryAgent")
