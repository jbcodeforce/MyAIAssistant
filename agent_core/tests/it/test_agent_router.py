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
from agent_core.agents.base_agent import AgentInput, AgentResponse
from agent_core.agents.agent_factory import get_agent_factory
from .conftest import (
    requires_local_server,
    requires_local_model
)

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")




@pytest.mark.integration
@requires_local_server
@requires_local_model
class TestAgentRouter:


    @pytest.mark.asyncio
    async def test_classify_code_help_query(self):
        """Test classification of a code help query."""
        query = "How do I implement a REST API endpoint in Python using FastAPI?"
        factory = get_agent_factory()
        router = factory.create_agent("AgentRouter")
        response = await router.execute(AgentInput(query=query)) 
        print(f"\n----\n{json.dumps(response.__dict__, indent=2, default=str)}\n----\n")
 
      

   