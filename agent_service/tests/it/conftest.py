"""Pytest fixtures for agent_service integration tests. Require a running server (e.g. on port 8100)."""

import os
import pytest_asyncio
from httpx import AsyncClient

# Default: http://127.0.0.1:8100. Override with AGENT_SERVICE_URL (e.g. http://localhost:8100).
_BASE_URL = os.environ.get("AGENT_SERVICE_URL", "http://127.0.0.1:8100").rstrip("/")


@pytest_asyncio.fixture
async def client():
    """Async HTTP client that connects to the running agent_service."""
    async with AsyncClient(base_url=_BASE_URL, timeout=30.0) as ac:
        yield ac