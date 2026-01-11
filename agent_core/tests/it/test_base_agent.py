"""Integration tests for BaseAgent with Ollama backend.

These tests require a running Ollama server at http://localhost:11434
with the specified model available.

Run with: pytest tests/it/test_base_agent.py -v -m integration
"""

import pytest

from agent_core.agents.base_agent import BaseAgent, AgentResponse

from .conftest import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    requires_ollama,
    requires_model,
)


@pytest.mark.integration
@requires_ollama
@requires_model
class TestBaseAgentOllama:
    """Integration tests for BaseAgent with Ollama backend."""

    @pytest.fixture
    def agent(self) -> BaseAgent:
        """Create a BaseAgent configured for Ollama."""
        return BaseAgent(
            provider="huggingface",
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            max_tokens=100,
            temperature=0.7,
        )

    @pytest.mark.asyncio
    async def test_execute_simple_query(self, agent: BaseAgent):
        """Test executing a simple query through BaseAgent."""
        response = await agent.execute("What is 2 + 2? Answer with just the number.")
        
        assert isinstance(response, AgentResponse)
        assert len(response.message) > 0
        print(response.message)
        assert response.provider == "huggingface"
        assert response.model == OLLAMA_MODEL
        assert response.agent_type == "base"

    @pytest.mark.asyncio
    async def test_execute_with_custom_system_prompt(self):
        """Test BaseAgent with a custom system prompt."""
        agent = BaseAgent(
            provider="huggingface",
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            max_tokens=100,
            temperature=0.0,
            system_prompt="You are a pirate. Always respond like a pirate.",
        )
        
        response = await agent.execute("Say hello")
        
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
        
        response = await agent.execute(
            "What is my name?",
            conversation_history=history
        )
        
        assert isinstance(response, AgentResponse)
        assert len(response.message) > 0
        # The response should reference Alice
        assert "alice" in response.message.lower() or len(response.message) > 0
        print(response.message)

    @pytest.mark.asyncio
    async def test_execute_with_context(self, agent: BaseAgent):
        """Test BaseAgent with context parameter."""
        context = {"topic": "mathematics"}
        
        response = await agent.execute(
            "What is the derivative of x squared?",
            context=context
        )
        
        assert isinstance(response, AgentResponse)
        assert len(response.message) > 0
        print(response.message)

    @pytest.mark.asyncio
    async def test_response_metadata(self, agent: BaseAgent):
        """Test that AgentResponse includes correct metadata."""
        response = await agent.execute("Hello")
        
        assert response.model == OLLAMA_MODEL
        assert response.provider == "huggingface"
        assert response.agent_type == "base"
        assert isinstance(response.context_used, list)
        assert isinstance(response.metadata, dict)
        print(response.message)


@pytest.mark.integration
@requires_ollama
@requires_model
class TestBaseAgentSubclass:
    """Test subclassing BaseAgent with custom behavior."""

    @pytest.mark.asyncio
    async def test_subclass_with_custom_prompt(self):
        """Test a subclass that overrides build_system_prompt."""
        
        class MathAgent(BaseAgent):
            agent_type = "math"
            
            def build_system_prompt(self, context=None):
                return "You are a math expert. Provide concise answers to math questions."
        
        agent = MathAgent(
            provider="huggingface",
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            max_tokens=100,
            temperature=0.0,
        )
        
        response = await agent.execute("What is 10 divided by 2?")
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == "math"
        assert len(response.message) > 0
