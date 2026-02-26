"""Integration tests for note parser agent: 
1. Classify query to determine intent
2. Route query to appropriate agent
3. Execute agent and return response
"""

import pytest
import json
from pathlib import Path
from agent_core.agents.agent_factory import AgentFactory

from agent_core.agents.note_parser_agent import NoteParserAgent, NoteParserResponse
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
class TestNoteParserAgent:


    @pytest.mark.asyncio
    async def test_note_parser_returns_structured_response(self):
        data_dir = Path(__file__).parent / "data"
        note_path = data_dir / "note.md"
        query = note_path.read_text().strip()
        factory = get_agent_factory()
        agent = factory.create_agent("NoteParserAgent")

        response = await agent.execute(AgentInput(query=query)) 
        print(f"\n----\n{json.dumps(response.__dict__, indent=2, default=str)}\n----\n")
        assert response.organization is not None
        assert response.persons is not None
        assert len(response.persons) == 1
        assert response.persons[0].name == "Matt TheBuilder"
        assert response.persons[0].role == "Confluent Champion"
        assert response.persons[0].context == None

        
 
      

   