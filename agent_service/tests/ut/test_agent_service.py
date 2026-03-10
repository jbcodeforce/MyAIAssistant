
from agent_service.main import agents
import pytest
from agno.agent import Agent, RemoteAgent
from agent_service.agents.agent_factory import get_or_create_agent_factory, reset_agent_factory
import os
from agent_service.agents.base_ai_agent import AIAgent
os.environ["AGENT_SERVICE_URL"] = "http://localhost:8100"


@pytest.mark.asyncio
async def test_singleton():
    factory = get_or_create_agent_factory()
    factory2 = get_or_create_agent_factory()
    assert factory is factory2
    reset_agent_factory()
    factory3 = get_or_create_agent_factory()
    assert factory is not factory3

@pytest.mark.asyncio
async def test_load_agent_refs():
    factory = get_or_create_agent_factory()
    refs = factory.get_agent_references()
    print(refs)
    assert len(refs) > 1
    for ref in refs:
        assert ref.agent_name is not None
        assert ref.description is not None
        assert ref.path_to_config is not None
        assert ref.url is not None
        assert ref.default is not None



@pytest.mark.asyncio
def test_load_agno_agents():
    factory = get_or_create_agent_factory()
    agents = factory.list_agents()
    assert len(agents) > 1
    print(agents)
    for agent in agents:
        assert isinstance(agent, Agent)
        assert agent.name is not None
    assert len(factory._ai_agents) > 1


@pytest.mark.asyncio
async def test_create_agent_router():
    factory = get_or_create_agent_factory()
    router = factory.get_or_create_agent("MainAgent")
    assert router is not None
    assert router.name == "MainAgent"
    assert router.db is not None



async def test_get_ai_agent():
    factory = get_or_create_agent_factory()
    ai_agent = factory.get_ai_agent("MainAgent")
    assert ai_agent is not None
    assert isinstance(ai_agent, AIAgent)
    assert ai_agent.get_agent() is not None
    assert ai_agent.get_system_prompt() is not None

