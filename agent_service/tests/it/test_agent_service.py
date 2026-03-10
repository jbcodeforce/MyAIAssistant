"""Integration tests for agent_service. Run against a live server with: AGENT_SERVICE_URL=http://localhost:8100 pytest ..."""

import json
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """GET / returns AgentOS API info (id, name, version)."""
    response = await client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("id") == "myai-agent-service"
    assert "version" in data
    assert data.get("name") == "AgentOS API"


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
async def test_agno_agent_runs(client: AsyncClient):
    """POST /agents/MainAgent/runs expects form data (message, stream=false for JSON response)."""
    response = await client.post(
        "/agents/MainAgent/runs",
        data={"message": "Hello, how are you?", "stream": "false"},
        timeout=60.0,
    )
    print(response.text)

async def _parse_sse_stream(line_stream):
    """Parse Server-Sent Events from an async line iterator. Yields (event_type, data_dict) tuples."""
    event_type = None
    data_buf = []
    async for line in line_stream:
        line = line.rstrip("\r\n") if isinstance(line, str) else line.decode("utf-8").rstrip("\r\n")
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_buf.append(line[5:].strip())
        elif line == "" and (event_type or data_buf):
            data_str = "\n".join(data_buf) if data_buf else "{}"
            try:
                data = json.loads(data_str) if data_str else {}
            except json.JSONDecodeError:
                data = {"raw": data_str}
            yield (event_type or "message", data)
            event_type = None
            data_buf = []


@pytest.mark.asyncio
async def test_simple_reasoning(client: AsyncClient):
    """POST /agents/MainAgent/runs with stream=true returns SSE (HTTP) stream; consume events and assert RunStarted/RunCompleted.
    AgentOS streams agent runs via Server-Sent Events; WebSocket is only used for workflows (/workflows/ws)."""
    task_description = (
        "Three missionaries and three cannibals need to cross a river. "
        "They have a boat that can carry up to two people at a time. "
        "If cannibals outnumber missionaries on either side, the cannibals eat the missionaries. "
        "How can all six get across safely? Reply in one short sentence."
    )
    events = []
    print(f"Running test_simple_reasoning with task_description:\n {task_description}")
    async with client.stream(
        "POST",
        "/agents/MainAgent/runs",
        data={"message": task_description, "stream": "true", "session_id": "test_session_id_123", "user_id": "test_user_id_123"},
        timeout=90.0,
    ) as response:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.read()}"
        async for event_type, data in _parse_sse_stream(response.aiter_lines()):
            events.append((event_type, data))
    assert len(events) >= 1, "Expected at least one SSE event"
    event_names = [e[0] for e in events]
    assert "RunStarted" in event_names, f"Expected RunStarted in {event_names}"
    last_event = events[-1]  # the last event is a string
    print(last_event) # tuple(str, dict)
    payload_dict = last_event[1]
    print(payload_dict)
    print("-"*40)
    session_id = payload_dict["session_id"]
    content = payload_dict["content"]
    assert content is not None

    print(f"Getting run details for session_id: {session_id}")
    print(f"URL: /agents/MainAgent/runs/?session_id={session_id}")
    response = await client.get(f"/agents/MainAgent/runs/?session_id={session_id}")
    print(f"Response: {response.text}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    print(json.dumps(data, indent=2))


