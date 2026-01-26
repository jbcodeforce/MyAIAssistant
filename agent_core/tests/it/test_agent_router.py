"""Integration tests for agent routing: 
1. Classify query to determine intent
2. Route query to appropriate agent
3. Execute agent and return response
"""

import pytest
import json
from pathlib import Path
from agent_core.agents.agent_factory import AgentFactory
from agent_core.agents.query_classifier import (
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
)
from agent_core.agents.agent_router import AgentRouter
from agent_core.agents.base_agent import BaseAgent, AgentInput, AgentResponse
from .conftest import (
    LOCAL_BASE_URL,
    LOCAL_MODEL,
    requires_ollama,
    requires_model,
)

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")


@pytest.fixture
def classifier() -> QueryClassifier:
    """Create a QueryClassifier with Ollama config."""
    factory = AgentFactory()
    classifier = factory.create_agent("QueryClassifier")
    return classifier

@pytest.mark.integration
@requires_ollama
@requires_model
class TestAgentRouter:


    @pytest.mark.asyncio
    async def test_classify_code_help_query(self, classifier: QueryClassifier):
        """Test classification of a code help query."""
        query = "How do I implement a REST API endpoint in Python using FastAPI?"
        router = AgentRouter()
        response = await router.route(query)    
        print(json.dumps(response.__dict__, indent=2, default=str))
      

   