"""Unit tests for TaskTaggingAgent."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock

from agent_core.agents.agent_factory import AgentFactory
from agent_core.agents.base_agent import AgentInput
from agent_core.agents.task_tagging_agent import TaskTaggingAgent


config_dir = str(Path(__file__).parent.parent.parent / "agent_core" / "agents" / "config")


class TestTaskTaggingAgent:
    """Tests for TaskTaggingAgent."""

    def test_factory_creates_task_tagging_agent(self):
        """TaskTaggingAgent is available from factory."""
        factory = AgentFactory(config_dir=config_dir)
        assert "TaskTaggingAgent" in factory.list_agents()
        agent = factory.create_agent("TaskTaggingAgent")
        assert isinstance(agent, TaskTaggingAgent)

    def test_parse_tags_from_response_json_block(self):
        """_parse_tags_from_response extracts tags from JSON code block."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("TaskTaggingAgent")
        text = 'Here are the tags:\n```json\n{"tags": ["planning", "code"], "reasoning": "..."}\n```'
        tags = agent._parse_tags_from_response(text)
        assert set(tags) == {"planning", "code"}
        assert len(tags) == 2

    def test_parse_tags_from_response_inline_json(self):
        """_parse_tags_from_response extracts tags from inline JSON."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("TaskTaggingAgent")
        text = 'Assigned: {"tags": ["research"]}'
        tags = agent._parse_tags_from_response(text)
        assert tags == ["research"]

    def test_parse_tags_from_response_empty(self):
        """_parse_tags_from_response returns empty list for empty or invalid text."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("TaskTaggingAgent")
        assert agent._parse_tags_from_response("") == []
        assert agent._parse_tags_from_response("no json here") == []

    @pytest.mark.asyncio
    async def test_execute_without_tool_provider_returns_error_metadata(self):
        """Execute without tool_provider returns response with error in metadata."""
        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("TaskTaggingAgent")
        assert agent._tool_provider is None
        response = await agent.execute(AgentInput(query="Tag this task.", context={}))
        assert response.agent_type in ("task_tagging", "TaskTaggingAgent")
        assert response.metadata.get("tags") == []
        assert response.metadata.get("error") == "tool_provider required"
        assert "tool_provider" in response.message

    @pytest.mark.asyncio
    async def test_execute_with_mock_tool_provider_and_mock_sdk_returns_tags(self):
        """Execute with mock tool_provider and mocked SDK query returns tags in metadata."""
        try:
            from claude_agent_sdk import AssistantMessage, TextBlock
        except ImportError:
            pytest.skip("claude-agent-sdk not installed")

        mock_provider = AsyncMock()
        mock_provider.get_available_tags = AsyncMock(return_value=["planning", "code"])
        mock_provider.task_list = AsyncMock(return_value=[{"id": 1, "title": "Task", "tags": ""}])
        mock_provider.update_task = AsyncMock(return_value={"success": True, "tags": "planning,code"})

        factory = AgentFactory(config_dir=config_dir)
        agent = factory.create_agent("TaskTaggingAgent", tool_provider=mock_provider)

        # Build message with required model kwarg if SDK expects it
        try:
            msg = AssistantMessage(content=[TextBlock(text='{"tags": ["planning", "code"]}')], model="test")
        except TypeError:
            msg = AssistantMessage(content=[TextBlock(text='{"tags": ["planning", "code"]}')])

        async def fake_query(prompt, options):
            yield msg

        import agent_core.agents.task_tagging_agent as task_mod
        original_query = task_mod.query
        task_mod.query = fake_query
        try:
            response = await agent.execute(
                AgentInput(query="Tag this task.", context={"todo_id": 1})
            )
            assert response.agent_type in ("task_tagging", "TaskTaggingAgent")
            assert "planning" in response.metadata.get("tags", [])
            assert "code" in response.metadata.get("tags", [])
        finally:
            task_mod.query = original_query
