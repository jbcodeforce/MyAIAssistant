
import pytest
from httpx import AsyncClient
from agent_service.agents.agent_factory import get_or_create_agent_factory
import os
os.environ["AGENT_SERVICE_URL"] = "http://localhost:8100"

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """GET / returns service info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert data.get("id") == "myai-agent-service"
    assert "version" in data

@pytest.mark.asyncio
async def test_get_list_agents(client: AsyncClient):
    """GET /agents returns list of agents (same as curl -X GET http://localhost:8100/agents)."""
    response = await client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_list_agent_names(client: AsyncClient):
    """GET /agents returns list of agent names (same as curl -X GET http://localhost:8100/agents)."""
    response = await client.get("/myai/agents")
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert isinstance(data, list)
    assert len(data) > 0

@pytest.mark.asyncio
async def test_create_agent_router():
    factory = get_or_create_agent_factory()
    router = factory.get_or_create_agent("MainAgent")
    assert router is not None
    response = router.run("Hello, how are you?")
    print(response.content)
    assert response.content is not None


@pytest.mark.asyncio
async def _test_agno_agent_runs(client: AsyncClient):
    """POST /agents/chat-agent/runs expects form data (message, stream=false for JSON response)."""
    response = await client.post(
        "/agents/chat-agent/runs",
        data={"message": "Hello, how are you?", "stream": "false"},
        timeout=60.0,
    )
    print(response.text)

@pytest.mark.asyncio
async def _test_agno_agent_runs(client: AsyncClient):
    """POST /agents/chat-agent/runs expects form data (message, stream=false for JSON response)."""
    response = await client.post(
        "/agents/chat-agent/runs",
        data={"message": "Hello, how are you?", "stream": "false"},
        timeout=60.0,
    )
    print(response.text)
    assert response.status_code == 200
    data = response.json()
    assert data is not None
