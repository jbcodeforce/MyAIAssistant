"""Tests for agent framework components."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import json


from agent_core.agents.agent_config import AgentConfig, LOCAL_MODEL, LOCAL_BASE_URL
from agent_core.types import LLMResponse
from agent_core.agents.agent_factory import AgentFactory, get_agent_factory
from agent_core.agents.base_agent import AgentInput, AgentResponse, BaseAgent
from agent_core.agents._llm_default import DefaultHFAdapter, LLMCallable


config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

class TestBaseAgent:
    """Tests for BaseAgent abstract class."""
    
    @pytest.fixture
    def agent(self) -> BaseAgent:
        """Create a BaseAgent configured for Ollama."""
        factory = get_agent_factory()
        return factory.create_agent("GeneralAgent")
    
    def test_create_base_agent(self):
        """Test creating a base agent."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("GeneralAgent")
        assert isinstance(agent, BaseAgent)
        assert agent._config.model == LOCAL_MODEL
        assert agent._config.temperature == 0.4
        assert agent._config.max_tokens == 4096
        assert agent._config.sys_prompt is not None
        assert agent._llm_client is not None
        assert isinstance(agent._llm_client, DefaultHFAdapter)
        assert len(agent._config.sys_prompt) > 10
        assert "helpful ai assistant" in agent._config.sys_prompt.lower()


    @pytest.mark.asyncio
    async def test_execute_agent_integration_point(self, agent: BaseAgent):
        """Test the execute method up to the LLM call logic with minimal patching."""

        # Save the original build messages to ensure message pipeline is exercised
        original_build_messages = agent._build_messages

        # Patch the LLM client's chat_async method so everything else is real
        call_llm_called = {}
        async def mock_chat_async(messages, config):
            # Message construction must have occurred
            assert messages is not None
            assert isinstance(messages, list)
            # Each message must be a dict with content
            assert any("python" in msg.get("content", "").lower() for msg in messages)
            call_llm_called["called"] = True
            # Simulate plausible model output
            from agent_core.types import LLMResponse
            return LLMResponse(
                content="Python is a high-level programming language known for its simplicity and readability.",
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
            )
        agent._llm_client.chat_async = mock_chat_async

        input_obj = AgentInput(query="What is Python?")
        response = await agent.execute(input_obj)

        # Check the returned response structure
        assert response is not None
        assert isinstance(response, AgentResponse)
        assert response.message is not None
        print(response.message)
        assert "python" in response.message.lower()
        assert "high-level" in response.message.lower()
        assert call_llm_called.get("called", False), "LLM client chat_async should have been invoked"
        # Important: check that the response context/metadata are present (empty or otherwise)
        assert hasattr(response, "context_used")
        assert hasattr(response, "metadata")
        # Spot check that messages are actually routed toward the LLM client
        # (i.e., agent internals construct chain works as expected)
        # Optionally re-invoke with a real _build_messages to further test message construction logic
        agent._build_messages = original_build_messages


   
class TestTaskAgent:
    """Tests for TaskAgent class."""
    
    @pytest.mark.asyncio
    async def test_build_messages_task_agent(selft):
        """Test building messages for a base agent."""
        factory = get_agent_factory()
        agent = factory.create_agent("TaskAgent")
        prompt = agent.build_system_prompt(context={"task_title": "Task 1", "task_description": "Task 1 description"})
        print(f"System prompt: {prompt}\n-------")
        messages = await agent._build_messages(AgentInput(query="What is the capital of France?", 
                            context={"task_title": "Task 1", "task_description": "Task 1 description"}))
        import json
        print(json.dumps(messages, indent=2, default=str))


    @pytest.mark.asyncio
    async def test_create_execute_task_agent(self):
        """Test creating a task agent."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("TaskAgent")
        context = {"task_title": "research environment content", "task_description": "search to build an environment engineering curriculum"}
        
        # Mock the LLM client's chat_async method
        from agent_core.types import LLMResponse
        async def mock_chat_async(messages, config):
            return LLMResponse(
                content="do this and that",
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            )
        agent._llm_client.chat_async = mock_chat_async
      
        response = await agent.execute(AgentInput(query="help me decompose this task", context=context))
        assert response is not None
        print(json.dumps(response.__dict__, indent=2, default=str))


class TestNoteParserAgent:
    """Tests for NoteParserAgent."""

    def test_factory_creates_note_parser_agent(self):
        """NoteParserAgent is available from factory (config_dir or defaults)."""
        factory = AgentFactory(config_dir=config_dir)
        assert "NoteParserAgent" in factory.list_agents()
        agent = factory.create_agent("NoteParserAgent")
        from agent_core.agents.note_parser_agent import NoteParserAgent, NoteParserResponse
        assert isinstance(agent, NoteParserAgent)

    @pytest.mark.asyncio
    async def test_note_parser_returns_structured_response(self):
        """NoteParserAgent returns NoteParserResponse with organization, persons, project, meetings when LLM returns valid JSON."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("NoteParserAgent")
        from agent_core.agents.note_parser_agent import NoteParserResponse

        valid_json = json.dumps({
            "organization": {"name": "Acme", "description": "A company"},
            "persons": [{"name": "John", "role": "Engineer", "context": None}],
            "project": {
                "name": "Acme engagement",
                "description": None,
                "past_steps": [{"what": "Met", "who": "John"}],
                "next_steps": [],
            },
            "meetings": [{"title": "Discovery", "content": "Notes here"}],
        })

        async def mock_chat_async(messages, config):
            return LLMResponse(
                content=valid_json,
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
            )

        agent._llm_client.chat_async = mock_chat_async
        response = await agent.execute(AgentInput(query="# Acme\n## Team\n* John: Engineer"))

        assert isinstance(response, NoteParserResponse)
        assert response.organization is not None
        assert response.organization.name == "Acme"
        assert response.organization.description == "A company"
        assert len(response.persons) == 1
        assert response.persons[0].name == "John"
        assert response.persons[0].role == "Engineer"
        assert response.project is not None
        assert response.project.name == "Acme engagement"
        assert len(response.project.past_steps) == 1
        assert response.project.past_steps[0].what == "Met"
        assert response.project.past_steps[0].who == "John"
        assert len(response.meetings) == 1
        assert response.meetings[0].title == "Discovery"
        assert response.meetings[0].content == "Notes here"
        assert response.parse_error is None
        assert response.metadata.get("parsed_successfully") is True

    @pytest.mark.asyncio
    async def test_index_parser_parse_error_on_malformed_json(self):
        """IndexParserAgent sets parse_error when LLM response is not valid JSON."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("NoteParserAgent")
        from agent_core.agents.note_parser_agent import NoteParserResponse

        async def mock_chat_async(messages, config):
            return LLMResponse(
                content="This is not JSON at all",
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            )

        agent._llm_client.chat_async = mock_chat_async
        response = await agent.execute(AgentInput(query="# Acme"))

        assert isinstance(response, NoteParserResponse)
        assert response.parse_error is not None
        assert "JSON" in response.parse_error or "Parse" in response.parse_error
        assert response.organization is None
        assert response.persons == []
        assert response.metadata.get("parsed_successfully") is False