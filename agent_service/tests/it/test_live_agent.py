"""Live integration tests for agent_service — require a running agent service AND a reachable LLM.

These tests are gated on the LLM_BASE_URL environment variable and carry the `live` pytest mark.
They are skipped automatically in CI (where LLM_BASE_URL is unset).

Run locally:
    LLM_BASE_URL=http://10.0.0.148/v1 pytest tests/it/test_live_agent.py -m live -v
"""

import os
import json
import pytest
from httpx import AsyncClient

LLM_REACHABLE = bool(os.getenv("LLM_BASE_URL"))
skip_no_llm = pytest.mark.skipif(
    not LLM_REACHABLE,
    reason="LLM_BASE_URL not set — skipping live LLM tests",
)


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


@skip_no_llm
@pytest.mark.live
@pytest.mark.asyncio
async def test_json_body_run_non_stream(client: AsyncClient):
    """POST JSON with stream=false to /agents/MainAgent/runs; assert 200 and non-empty content."""
    response = await client.post(
        "/agents/MainAgent/runs",
        json={"message": "Say hello in one sentence.", "stream": "false"},
        timeout=60.0,
    )
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    # Response may be a dict with 'content' or 'messages'; accept either shape.
    content = data.get("content") or data.get("messages")
    assert content, f"Expected non-empty content/messages in response, got: {data}"


@skip_no_llm
@pytest.mark.live
@pytest.mark.asyncio
async def test_json_body_run_stream(client: AsyncClient):
    """POST JSON with stream=true to /agents/MainAgent/runs; assert SSE events include RunContent and RunCompleted."""
    events = []
    async with client.stream(
        "POST",
        "/agents/MainAgent/runs",
        json={
            "message": "Say hello in one sentence.",
            "stream": "true",
            "session_id": "live-test-session",
        },
        timeout=60.0,
    ) as response:
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.read()}"
        )
        async for event_type, data in _parse_sse_stream(response.aiter_lines()):
            events.append((event_type, data))

    event_names = [e[0] for e in events]
    assert any(name == "RunContent" for name in event_names), (
        f"Expected at least one RunContent event; got: {event_names}"
    )
    assert "RunCompleted" in event_names, (
        f"Expected RunCompleted event; got: {event_names}"
    )


@skip_no_llm
@pytest.mark.live
@pytest.mark.asyncio
async def test_myai_agents_url_shape(client: AsyncClient):
    """GET /myai/agents; assert 200, non-empty list, all agent URLs end with /runs (not /stream)."""
    response = await client.get("/myai/agents")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    agents = response.json()
    assert isinstance(agents, list) and len(agents) >= 1, (
        f"Expected non-empty list of agents, got: {agents}"
    )
    for agent in agents:
        url = agent.get("url", "")
        if url:
            assert not url.endswith("/stream"), (
                f"Agent URL must not end with /stream: {url}"
            )
            assert url.endswith("/runs"), (
                f"Agent URL must end with /runs: {url}"
            )
