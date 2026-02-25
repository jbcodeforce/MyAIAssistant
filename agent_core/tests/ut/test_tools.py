import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import json

from agent_core.agents.agent_config import AgentConfig
from agent_core.agents.base_agent import BaseAgent, AgentInput, AgentResponse
from agent_core.agents.tool_registry import ToolRegistry, tool, get_global_tool_registry
from agent_core.types import LLMResponse, ToolCall, ToolOutput, Message
from agent_core.agents._llm_default import DefaultHFAdapter

# Define a dummy tool for testing
# These tools are defined in agent_core/agents/tools/calculator_tools.py
# and registered globally. We don't need to redefine them here.

class TestToolRegistry:
    def test_register_and_get_tool(self):
        registry = ToolRegistry()
        
        async def dummy_func(x, y): return x + y
        registry.register_tool("dummy_tool", dummy_func)
        
        retrieved_func = registry.get_tool("dummy_tool")
        assert retrieved_func == dummy_func
        
    def test_get_non_existent_tool(self):
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="Tool 'non_existent_tool' not found"):
            registry.get_tool("non_existent_tool")
            
    def test_tool_decorator(self):
        # The test_add and test_multiply tools are registered globally
        registry = get_global_tool_registry()
        # Assuming 'test_add' and 'test_multiply' are registered elsewhere (e.g., in calculator_tools.py)
        # For this test, we'll register a dummy one to ensure the decorator works
        @tool("dummy_decorated_tool")
        async def dummy_decorated_tool_func(): pass
        
        assert "dummy_decorated_tool" in registry
        assert registry.get_tool("dummy_decorated_tool").__name__ == "dummy_decorated_tool_func"
        
        # Check for the calculator tools if they are imported and registered
        # This depends on agent_core.agents.__init__ importing calculator_tools
        from agent_core.agents.tools import calculator_tools # Ensure import for registration
        assert "add" in registry # 'add' is the name used in calculator_tools.py
        assert registry.get_tool("add").__name__ == "add"


class TestAgentConfigTools:
    def test_load_tools_from_yaml(self, tmp_path):
        yaml_content = """
        name: TestAgentWithTools
        description: An agent with tools
        model: test-model
        tools:
          - type: function
            function:
              name: test_add
              description: Adds two numbers
              parameters:
                type: object
                properties:
                  a: {type: number}
                  b: {type: number}
                required: [a, b]
        tool_choice: auto
        """
        config_file = tmp_path / "agent.yaml"
        config_file.write_text(yaml_content)
        
        config = AgentConfig.from_yaml(config_file)
        
        assert config.name == "TestAgentWithTools"
        assert config.model == "test-model"
        assert config.tools is not None
        assert len(config.tools) == 1
        assert config.tools[0]["function"]["name"] == "test_add"
        assert config.tool_choice == "auto"

    def test_load_no_tools_from_yaml(self, tmp_path):
        yaml_content = """
        name: TestAgentNoTools
        description: An agent without tools
        model: test-model
        """
        config_file = tmp_path / "agent.yaml"
        config_file.write_text(yaml_content)
        
        config = AgentConfig.from_yaml(config_file)
        
        assert config.name == "TestAgentNoTools"
        assert config.tools is None
        assert config.tool_choice is None

class TestBaseAgentToolHandling:
    @pytest.fixture
    def mock_llm_client(self):
        mock = AsyncMock(spec=DefaultHFAdapter)
        mock.chat_async.return_value = LLMResponse(
            content="Hello from LLM",
            model="mock-model",
            provider="mock-provider"
        )
        return mock

    @pytest.fixture
    def agent_with_tools(self, mock_llm_client):
        config = AgentConfig(
            name="ToolUserAgent",
            model="mock-model",
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "test_add",
                        "description": "Adds two integers.",
                        "parameters": {
                            "type": "object",
                            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                            "required": ["a", "b"],
                        },
                    },
                }
            ],
            tool_choice="auto"
        )
        return BaseAgent(config=config, llm_client=mock_llm_client)

    @pytest.mark.asyncio
    async def test_handle_tool_call(self, agent_with_tools):
        tool_call = ToolCall(id="call_123", function_name="test_add", arguments={"a": 5, "b": 3})
        output = await agent_with_tools._handle_tool_call(tool_call)
        
        assert isinstance(output, ToolOutput)
        assert output.tool_call_id == "call_123"
        assert output.output == "8" # Result of test_add(5, 3)

    @pytest.mark.asyncio
    async def test_handle_tool_call_non_existent_tool(self, agent_with_tools):
        tool_call = ToolCall(id="call_456", function_name="non_existent_tool", arguments={})
        output = await agent_with_tools._handle_tool_call(tool_call)
        
        assert isinstance(output, ToolOutput)
        assert output.tool_call_id == "call_456"
        assert "Error: Tool 'non_existent_tool' not found" in output.output

    @pytest.mark.asyncio
    async def test_execute_with_llm_returning_final_answer(self, agent_with_tools, mock_llm_client):
        mock_llm_client.chat_async.return_value = LLMResponse(
            content="The answer is 8.",
            model="mock-model",
            provider="mock-provider"
        )
        
        input_data = AgentInput(query="What is 5 + 3?")
        response = await agent_with_tools.execute(input_data)
        
        assert response.message == "The answer is 8."
        mock_llm_client.chat_async.assert_called_once()
        args, kwargs = mock_llm_client.chat_async.call_args
        assert kwargs["tools"] is not None
        assert kwargs["tool_choice"] == "auto"
        assert any(msg.content == "What is 5 + 3?" for msg in args[0])

    @pytest.mark.asyncio
    async def test_execute_with_llm_returning_tool_call(self, agent_with_tools, mock_llm_client):
        # First LLM call returns a tool call
        mock_llm_client.chat_async.side_effect = [
            LLMResponse(
                content=None,
                model="mock-model",
                provider="mock-provider",
                tool_calls=[
                    ToolCall(id="call_123", function_name="test_add", arguments={"a": 5, "b": 3})
                ]
            ),
            # Second LLM call returns the final answer after tool execution
            LLMResponse(
                content="The sum of 5 and 3 is 8.",
                model="mock-model",
                provider="mock-provider"
            )
        ]
        
        input_data = AgentInput(query="What is 5 + 3?")
        response = await agent_with_tools.execute(input_data)
        
        assert response.message == "The sum of 5 and 3 is 8."
        assert mock_llm_client.chat_async.call_count == 2
        
        # Verify first call arguments
        first_call_args, first_call_kwargs = mock_llm_client.chat_async.call_args_list[0]
        assert first_call_kwargs["tools"] is not None
        assert first_call_kwargs["tool_choice"] == "auto"
        assert any(msg.content == "What is 5 + 3?" for msg in first_call_args[0])
        
        # Verify second call arguments (should include tool output)
        second_call_args, second_call_kwargs = mock_llm_client.chat_async.call_args_list[1]
        assert second_call_kwargs["tools"] is not None
        assert second_call_kwargs["tool_choice"] == "auto"
        
        # Check for tool message in the second call's messages
        tool_message_found = False
        for msg in second_call_args[0]:
            if msg.role == "tool" and msg.tool_call_id == "call_123" and msg.content == "8":
                tool_message_found = True
                break
        assert tool_message_found, "Tool output message not found in second LLM call"

    @pytest.mark.asyncio
    async def test_execute_with_llm_returning_tool_call_and_content(self, agent_with_tools, mock_llm_client):
        # LLM returns both content and a tool call (should prioritize tool call)
        mock_llm_client.chat_async.side_effect = [
            LLMResponse(
                content="I need to calculate this for you.",
                model="mock-model",
                provider="mock-provider",
                tool_calls=[
                    ToolCall(id="call_123", function_name="test_add", arguments={"a": 5, "b": 3})
                ]
            ),
            LLMResponse(
                content="The result is 8.",
                model="mock-model",
                provider="mock-provider"
            )
        ]
        
        input_data = AgentInput(query="Calculate 5 + 3.")
        response = await agent_with_tools.execute(input_data)
        
        assert response.message == "The result is 8."
        assert mock_llm_client.chat_async.call_count == 2
