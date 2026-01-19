

import pytest
from agent_core.agents.query_classifier import QueryClassifier
from agent_core.agents.factory import AgentFactory
from agent_core.agents.base_agent import AgentInput


class TestQueryClassifier:
    """Tests for the QueryClassifier class."""

    @pytest.fixture
    def real_factory(self):
        """Create factory pointing to real config directory."""
        return AgentFactory()

    def test_1_classify_meeting_notes(self, real_factory):
        """Test classifying a meeting notes query."""
        classifier = real_factory.create_agent("QueryClassifier")
        meeting_note = """
        ## Meeting 01/07
* Presents: William Chen, Christian Quebral,  Neil Hudson
* Issue with ARRAY_AGG function. In Java the Array_agg ROW seems to work
* Less degraded statement alert reported since beginning of the year. 
        """
        result = classifier.execute(AgentInput(query=meeting_note))
        print(result)
        assert result.confidence == 0.95
        assert result.reasoning == "The user is asking to process a meeting notes."
        assert result.entities == {"topic": "meeting notes", "action": "review"}
        assert result.suggested_context == "The user is asking to review a meeting notes document for summarize and build next steps."