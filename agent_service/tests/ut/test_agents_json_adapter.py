"""Unit tests for the JSON-to-form adapter on POST /agents/{name}/runs.

These tests run entirely in-process using ASGI test transport — no real LLM,
no real AgentOS, no network.  A stub FastAPI app simulates the AgentOS handler
so we can verify the adapter:

1. Re-encodes JSON bodies as form data and forwards them.
2. Passes form-encoded bodies through unchanged.
3. Propagates the upstream status code and headers back to the caller.
4. Correctly streams an SSE response body.
"""

import os
import pytest
import pytest_asyncio
from fastapi import FastAPI, Request, Form
from fastapi.responses import StreamingResponse
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("AGENT_SERVICE_PORT", "8100")


# ---------------------------------------------------------------------------
# Stub "AgentOS" app — form-encoded only, as the real AgentOS works.
# ---------------------------------------------------------------------------

_agentoss_stub = FastAPI(title="AgentOS Stub")


@_agentoss_stub.post("/agents/{agent_name}/runs")
async def _runs_stub(
    agent_name: str,
    message: str = Form(...),
    stream: str = Form("false"),
):
    if stream.lower() == "true":
        def _sse():
            yield "event: RunStarted\ndata: {}\n\n"
            yield f'event: RunContent\ndata: {{"content": "hello from {agent_name}"}}\n\n'
            yield 'event: RunCompleted\ndata: {"content": "done", "session_id": "s1"}\n\n'

        return StreamingResponse(_sse(), media_type="text/event-stream")
    return {"content": f"echo: {message}", "session_id": "s1"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def adapter_client(monkeypatch):
    """In-process client whose JSON adapter sub-requests hit the stub ASGI app.

    The adapter creates its own ``httpx.AsyncClient`` instances internally.
    We monkeypatch ``httpx.AsyncClient`` in the adapter module so that every
    instance transparently routes to the stub via ``ASGITransport``.
    """
    import agent_service.routes.agents as agents_mod
    import httpx

    stub_transport = ASGITransport(app=_agentoss_stub)

    original_async_client = httpx.AsyncClient

    class _StubClient(original_async_client):
        """Overrides transport so all requests go to the AgentOS stub."""
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = stub_transport
            kwargs["base_url"] = "http://127.0.0.1:8100"
            kwargs.pop("timeout", None)
            super().__init__(*args, timeout=None, **kwargs)

    monkeypatch.setattr(agents_mod.httpx, "AsyncClient", _StubClient)

    # Build an outer app containing only the adapter router.
    from agent_service.routes.agents import router as adapter_router
    outer_app = FastAPI(title="Outer")
    outer_app.include_router(adapter_router)

    transport = ASGITransport(app=outer_app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_json_body_non_stream_returns_200(adapter_client: AsyncClient):
    """POST JSON with stream=false → HTTP 200 and echoed content."""
    response = await adapter_client.post(
        "/agents/MainAgent/runs",
        json={"message": "hello", "stream": "false"},
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "content" in data
    assert "hello" in data["content"]


@pytest.mark.asyncio
async def test_json_body_stream_returns_sse(adapter_client: AsyncClient):
    """POST JSON with stream=true → SSE response with RunStarted and RunCompleted events."""
    async with adapter_client.stream(
        "POST",
        "/agents/MainAgent/runs",
        json={"message": "hi", "stream": "true"},
    ) as response:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type, f"Expected SSE content-type, got: {content_type}"
        raw = await response.aread()

    text = raw.decode("utf-8")
    assert "RunStarted" in text
    assert "RunCompleted" in text
    assert "RunContent" in text


@pytest.mark.asyncio
async def test_form_encoded_body_passes_through(adapter_client: AsyncClient):
    """POST with form-encoding (not JSON) is forwarded unchanged to the upstream handler."""
    response = await adapter_client.post(
        "/agents/MainAgent/runs",
        data={"message": "hello from form", "stream": "false"},
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "content" in data
    assert "hello from form" in data["content"]


@pytest.mark.asyncio
async def test_json_booleans_converted_to_strings(adapter_client: AsyncClient):
    """Boolean JSON values (true/false) are forwarded as strings the form handler can parse."""
    # Python bool False serialises to "False"; lowercase check means stream != "true" → no SSE.
    response = await adapter_client.post(
        "/agents/MainAgent/runs",
        json={"message": "bool test", "stream": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
