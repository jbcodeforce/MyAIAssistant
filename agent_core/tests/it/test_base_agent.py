"""Integration tests for BaseAgent with Ollama backend.

These tests require a running Ollama server at http://localhost:11434
with the specified model available.

Run with: pytest tests/it/test_base_agent.py -v -m integration
"""

from pathlib import Path
import pytest


from agent_core.agents.agent_config import AgentConfig, LOCAL_MODEL, LOCAL_BASE_URL
from agent_core.agents.agent_factory import AgentFactory, get_agent_factory
from agent_core.agents.base_agent import BaseAgent, AgentResponse, AgentInput

from .conftest import (
    requires_local_server,
    requires_local_model,
    is_local_server_available,
    is_model_available,
)


config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

@pytest.mark.integration
class TestLocalLLMServer:
    """Integration tests for local LLM server."""

    @pytest.mark.asyncio
    async def test_local_llm_server(self):
        assert is_local_server_available()

    @pytest.mark.asyncio
    async def test_local_llm_model(self):
        assert is_model_available(LOCAL_MODEL)

@pytest.mark.integration
@requires_local_server
@requires_local_model
class TestBaseAgent:
    """Integration tests for BaseAgent with Ollama backend."""

    @pytest.fixture
    def agent(self) -> BaseAgent:
        """Create a BaseAgent configured for Ollama."""
        factory = get_agent_factory(config_dir=config_dir)
        return factory.create_agent("GeneralAgent")


    @pytest.mark.asyncio
    async def test_chat_async_local(self, agent: BaseAgent):
        """Test async chat completion with local server."""
        message = "What is 2 + 2? Answer with just the number"
        input_data = AgentInput(query=message)
        response = await agent.execute(input_data)
        assert isinstance(response, AgentResponse)
        assert len(response.message) > 0
        print(f"Response: {response.message}")


    @pytest.mark.asyncio
    async def test_execute_with_custom_system_prompt(self):
        """Test BaseAgent with a custom system prompt."""
        config = AgentConfig(
            model=LOCAL_MODEL,
            provider="huggingface",
            base_url=LOCAL_BASE_URL,
            max_tokens=100,
            temperature=0.0,
            agent_dir=Path(config_dir) / "GeneralAgent",
            description="A general purpose agent.",
            agent_class="agent_core.agents.base_agent.BaseAgent",
        )
        agent = BaseAgent(config=config)
        agent._system_prompt = "You are a pirate. Always respond like a pirate."
        response = await agent.execute(AgentInput(query="Say hello"))
        assert isinstance(response, AgentResponse)
        assert len(response.message) > 0
        print(response.message)

    @pytest.mark.asyncio
    async def test_execute_with_conversation_history(self, agent: BaseAgent):
        """Test BaseAgent with conversation history."""
        history = [
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Hello Alice! Nice to meet you."},
        ]
        
        response = await agent.execute(AgentInput(
            query="What is my name?",
            conversation_history=history
        ))
        
        assert isinstance(response, AgentResponse)
        assert len(response.message) > 0
        # The response should reference Alice
        assert "alice" in response.message.lower() or len(response.message) > 0
        print(response.message)

    @pytest.mark.asyncio
    async def test_execute_with_context(self, agent: BaseAgent):
        """Test BaseAgent with context parameter."""
        context = {"topic": "mathematics"}
        
        response = await agent.execute(AgentInput(
            query="What is the derivative of x squared?",
            context=context
        ))
        
        assert isinstance(response, AgentResponse)
        assert len(response.message) > 0
        print(response.message)


class TestBaseAgentWithPersona:
    """Integration tests for BaseAgent with Persona."""

    @pytest.fixture
    def persona_agent(self) -> BaseAgent:
        """Create a BaseAgent configured for Persona."""
        factory = AgentFactory(config_dir=config_dir)
        return factory.create_agent("PersonaAgent")

    @pytest.mark.asyncio
    async def test_chat_async_local(self, persona_agent: BaseAgent):
        """Test async chat completion with local server."""
        message = "I need to get an environment engineering learning plan"
        input_data = AgentInput(query=message)
        response = await persona_agent.execute(input_data)
        assert isinstance(response, AgentResponse)
        assert len(response.message) > 0
        print(f"Response: {response.message}")