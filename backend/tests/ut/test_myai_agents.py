"""GET /api/myai/agents proxies to the agent service."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.myai_agents import router as myai_agents_router


def _app() -> FastAPI:
    a = FastAPI()
    a.include_router(myai_agents_router, prefix="/api")
    return a


@pytest.mark.asyncio
async def test_myai_agents_proxies_ok():
    payload = [
        {
            "agent_name": "MainAgent",
            "description": "d",
            "path_to_config": "x",
            "url": "http://localhost:8100/agents/MainAgent/runs",
            "default": True,
        }
    ]
    with patch(
        "app.api.myai_agents.list_myai_agents", new=AsyncMock(return_value=payload)
    ):
        transport = ASGITransport(app=_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/myai/agents")
    assert r.status_code == 200
    assert r.json() == payload


@pytest.mark.asyncio
async def test_myai_agents_502_on_request_error():
    with patch(
        "app.api.myai_agents.list_myai_agents",
        new=AsyncMock(side_effect=httpx.RequestError("boom", request=httpx.Request("GET", "http://t"))),
    ):
        transport = ASGITransport(app=_app())
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/myai/agents")
    assert r.status_code == 502
    assert "unreachable" in (r.json().get("detail") or "").lower()
