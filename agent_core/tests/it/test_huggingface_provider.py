"""Integration tests for default HuggingFace InferenceClient path.

These tests require either:
- A running local inference server (TGI, vLLM, or similar with OpenAI-compatible API)
- Valid HF_TOKEN for HuggingFace Hub access

Run with: pytest tests/it/test_huggingface_provider.py -v -m integration
"""

import os

import pytest
import httpx
from pathlib import Path

from agent_core.agents.agent_config import (
    AgentConfig,
    LOCAL_MODEL,
    LOCAL_BASE_URL,
    REMOTE_MODEL,
)
from agent_core.types import LLMResponse
from agent_core.agents._llm_default import DefaultHFAdapter

from .conftest import requires_local_server

config_dir = str(Path(__file__).parent.parent.parent / "agent_core" / "agents" / "config")
HF_TOKEN = os.getenv("HF_TOKEN")


def is_hf_token_valid() -> bool:
    """Check if HF_TOKEN is set and valid."""
    token = HF_TOKEN
    if not token:
        return False
    try:
        response = httpx.get(
            "https://huggingface.co/api/whoami",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


requires_hf_token = pytest.mark.skipif(
    not is_hf_token_valid(),
    reason="Valid HF_TOKEN not available",
)


@pytest.fixture
def local_config() -> AgentConfig:
    """Create AgentConfig for local inference server."""
    return AgentConfig(
        name="LocalHFTest",
        provider="huggingface",
        agent_dir=Path(config_dir) / "GeneralAgent",
        description="A general purpose agent.",
        agent_class="agent_core.agents.base_agent.BaseAgent",
        model=LOCAL_MODEL,
        base_url=LOCAL_BASE_URL,
        max_tokens=200,
        temperature=0.7,
        timeout=120.0,
    )


@pytest.fixture
def remote_config() -> AgentConfig:
    """Create AgentConfig for remote HuggingFace Hub."""
    return AgentConfig(
        name="RemoteHFTest",
        provider="huggingface",
        agent_dir=Path(config_dir) / "GeneralAgent",
        description="A general purpose agent.",
        agent_class="agent_core.agents.base_agent.BaseAgent",
        model=REMOTE_MODEL,
        base_url=None,
        api_key=HF_TOKEN,
        max_tokens=100,
        temperature=0.7,
        timeout=60.0,
    )


@pytest.fixture
def messages() -> list[dict]:
    """Create test messages (list[dict] for DefaultHFAdapter)."""
    return [
        {"role": "system", "content": "You are a helpful assistant. Keep responses brief."},
        {"role": "user", "content": "What is 2 + 2?"},
    ]


@pytest.mark.integration
@requires_local_server
class TestDefaultHFAdapterLocal:
    """Integration tests for default HF adapter with local inference server."""

    def test_chat_sync_local(self, local_config: AgentConfig, messages: list[dict]):
        """Test sync chat completion with local server."""
        adapter = DefaultHFAdapter()
        response = adapter.chat_sync(messages, config=local_config)
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0


@pytest.mark.integration
@requires_hf_token
class TestDefaultHFAdapterRemote:
    """Integration tests for default HF adapter with HF Hub (remote)."""

    @pytest.mark.asyncio
    async def test_chat_async_remote(
        self, remote_config: AgentConfig, messages: list[dict]
    ):
        """Test async chat completion with HF Hub."""
        adapter = DefaultHFAdapter()
        response = await adapter.chat_async(messages, config=remote_config)
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.provider == "huggingface"
        if response.usage:
            assert response.prompt_tokens >= 0
            assert response.completion_tokens >= 0

    def test_chat_sync_remote(
        self, remote_config: AgentConfig, messages: list[dict]
    ):
        """Test sync chat completion with HF Hub."""
        adapter = DefaultHFAdapter()
        response = adapter.chat_sync(messages, config=remote_config)
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.provider == "huggingface"
        if response.usage:
            assert response.prompt_tokens >= 0
            assert response.completion_tokens >= 0
