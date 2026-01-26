"""Tests for agent framework components."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import json


from agent_core.agents.agent_factory import AgentConfig
from agent_core.types import LLMResponse
from agent_core.agents.agent_factory import AgentFactory
from agent_core.agents.base_agent import AgentInput, AgentResponse

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

class TestBaseAgent:
    """Tests for BaseAgent abstract class."""
    
    
    def test_create_base_agent(self):
        """Test creating a base agent."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("GeneralAgent")
        assert agent._config.model == "mistral:7b-instruct"
        assert agent._config.temperature == 0.7
        assert agent._config.max_tokens == 2048
        assert agent._system_prompt is not None
        assert "helpful ai assistant" in agent._system_prompt.lower()


    @pytest.mark.asyncio
    async def test_execute_agent(self):
        """Test executing a base agent."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("GeneralAgent")
        
        # Mock the _call_llm method to return a fake response
        agent._call_llm = AsyncMock(return_value="Python is a high-level programming language known for its simplicity and readability.")
        
        response = await agent.execute(AgentInput(query="What is Python?"))
        assert response is not None
        assert response.message is not None
        assert response.context_used is not None
        assert response.metadata is not None
        assert "python" in response.message.lower()
        assert "high-level" in response.message.lower()
        
        # Verify _call_llm was called
        agent._call_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_build_messages(self):
        """Test building messages for a base agent."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("TaskAgent")

        prompt = agent.build_system_prompt(context={"task_title": "Task 1", "task_description": "Task 1 description"})
        print(prompt)
        messages = await agent._build_messages(AgentInput(query="What is the capital of France?", 
                            context={"task_title": "Task 1", "task_description": "Task 1 description"}))
        import json
        print(json.dumps(messages, indent=2, default=str))

class TestTaskAgent:
    """Tests for TaskAgent class."""
    
    @pytest.mark.asyncio
    async def test_create_execute_task_agent(self):
        """Test creating a task agent."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("TaskAgent")
        context = {"task_title": "research environment content", "task_description": "search to build an environment engineering curriculum"}
        agent._call_llm = AsyncMock(return_value="do this and that")
      
        response = await agent.execute(AgentInput(query="help me decompose this task", context=context))
        assert response is not None
        print(json.dumps(response.__dict__, indent=2, default=str))