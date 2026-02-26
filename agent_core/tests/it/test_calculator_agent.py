import pytest
from agent_core.agents.agent_config import AgentConfig
from agent_core.agents.agent_factory import get_agent_factory
from agent_core.agents.base_agent import AgentInput, AgentResponse
from agent_core.agents.tool_registry import get_global_tool_registry
from .conftest import (
    requires_local_server,
    requires_local_model
)

# Ensure the tool is registered
from agent_core.agents.tools import calculator_tools

@pytest.mark.integration
@requires_local_server
@requires_local_model
class TestCalculatorAgent:

    @pytest.mark.asyncio
    async def test_add_operation(self):
        """Test the CalculatorAgent's add tool."""
        factory = get_agent_factory()
        config = AgentConfig(tool_choice="auto")
        calculator_agent = factory.create_agent("CalculatorAgent")
        
        query = "What is 10 + 25?"
        input_data = AgentInput(query=query)
        try:    
            response = await calculator_agent.execute(input_data)
        except Exception as e:
            print(f"Error: {e}")
            assert False
        
        assert isinstance(response, AgentResponse)
        assert "35" in response.message
        print(f"\nCalculatorAgent Response: {response.message}")

    @pytest.mark.asyncio
    async def test_add_operation_multiple_times(self):
        """Test the CalculatorAgent's add tool multiple times."""
        factory = get_agent_factory()
        calculator_agent = factory.create_agent("CalculatorAgent")
        
        queries = [
            ("What is 1 + 1?", "2"),
            ("Add 100 and 200.", "300"),
            ("Sum of 7 and 8?", "15"),
        ]

        for query, expected_result in queries:
            input_data = AgentInput(query=query)
            try:    
                response = await calculator_agent.execute(input_data)
            except Exception as e:
                print(f"Error: {e}")
                assert False
            
            assert isinstance(response, AgentResponse)
            assert expected_result in response.message
            print(f"\nCalculatorAgent Response for '{query}': {response.message}")

