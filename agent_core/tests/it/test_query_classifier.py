

import pytest
import json
from agent_core.agents.query_classifier import ClassificationResult, QueryIntent
from agent_core.agents.agent_factory import get_agent_factory
from agent_core.agents.base_agent import AgentInput
from pathlib import Path

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

class TestQueryClassifier:
    """Tests for the QueryClassifier class."""

    @pytest.mark.asyncio
    async def test_1_classify_meeting_notes(self):
        """Test classifying a meeting notes query."""
        real_factory = get_agent_factory(config_dir=config_dir)
        classifier = real_factory.create_agent("QueryClassifier")
        meeting_note = """
        ## Meeting 01/07
* Presents: William Chen, Christian Quebral,  Neil Hudson
* Issue with ARRAY_AGG function. In Java the Array_agg ROW seems to work
* Less degraded statement alert reported since beginning of the year. 
        """
        result = await classifier.execute(AgentInput(query=meeting_note))
        print(f"\n----\n{json.dumps(result.__dict__, default=str, indent=2)}\n----\n")
        assert isinstance(result, ClassificationResult)
        assert result.confidence >= 0.8
        assert result.intent in (
            QueryIntent.MEETING_NOTE,
            QueryIntent.KNOWLEDGE_SEARCH,
        ), "Meeting-style content may be classified as meeting_note or knowledge_search"
        assert result.reasoning is not None
        assert result.entities is not None
        assert result.entities.get("topic") is not None
        topic = result.entities.get("topic", "").lower()
        assert "function" in topic or "array_agg" in topic, f"Topic should reference meeting content, got {topic!r}"


    @pytest.mark.asyncio
    async def test_2_classify_research(self):
        """Test classifying research query."""
        real_factory =get_agent_factory(config_dir=config_dir)
        classifier = real_factory.create_agent("QueryClassifier")
        query = """
       I would like to know how to learn environment engineering using free sources
        """
        result = await classifier.execute(AgentInput(query=query))
        print(f"\n----\n{json.dumps(result.__dict__, default=str, indent=2)}\n----\n")
        assert isinstance(result, ClassificationResult)
        assert result.confidence >= 0.8
        assert result.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert result.reasoning is not None
        assert result.entities is not None
        assert result.entities.get("topic") is not None

    @pytest.mark.asyncio
    async def test_3_code_help(self):
        """Test classifying research query."""
        real_factory =get_agent_factory(config_dir=config_dir)
        classifier = real_factory.create_agent("QueryClassifier")
        query = """
       I would like to implement a REST API endpoint in FastAPI using a RAG approach
        """
        result = await classifier.execute(AgentInput(query=query))
        print(f"\n----\n{json.dumps(result.__dict__, default=str, indent=2)}\n----\n")
        assert isinstance(result, ClassificationResult)
        assert result.confidence >= 0.8
        assert result.intent in (
            QueryIntent.CODE_HELP,
            QueryIntent.TASK_PLANNING,
        ), "Implementation query may be classified as code_help or task_planning"
        assert result.reasoning is not None
        assert result.entities is not None
        assert result.entities.get("topic") is not None

    @pytest.mark.asyncio
    async def test_4_task_planning(self):
        """Test classifying research query."""
        real_factory =get_agent_factory(config_dir=config_dir)
        classifier = real_factory.create_agent("QueryClassifier")
        query = """
        what should I do to prepare for the interview next week?
        """
        result = await classifier.execute(AgentInput(query=query))
        print(json.dumps(result.__dict__, default=str, indent=2))
        assert isinstance(result, ClassificationResult)
        assert result.confidence >= 0.8
        assert result.intent == QueryIntent.TASK_PLANNING
        assert result.reasoning is not None
        assert result.entities is not None
        assert result.entities.get("topic") is not None