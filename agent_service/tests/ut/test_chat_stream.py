"""Unit tests for chat stream endpoint contract: multiple NDJSON content lines then done."""

import json
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from tests.ut.conftest import _make_app


@pytest_asyncio.fixture
async def client():
    """Client using stub app that streams multiple content chunks then done."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_chat_generic_stream_returns_incremental_chunks(client: AsyncClient):
    """POST /chat/generic/stream returns multiple NDJSON content lines before final done line."""
    response = await client.post(
        "/chat/generic/stream",
        json={"message": "Hi", "conversation_history": []},
        timeout=10.0,
    )
    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers.get("content-type", "")

    lines = [line for line in response.text.strip().split("\n") if line]
    assert len(lines) >= 2, "Expected at least 2 lines (content + done)"

    content_lines = []
    done_line = None
    for line in lines:
        obj = json.loads(line)
        if "content" in obj:
            content_lines.append(obj["content"])
        if obj.get("done"):
            done_line = obj

    assert len(content_lines) >= 2, "Expected multiple content chunks before done (incremental streaming)"
    assert done_line is not None, "Expected final line with done: true"
    assert done_line.get("done") is True
    assert content_lines[-1] != "" or len(content_lines) > 2, "Expected non-empty content chunks"
