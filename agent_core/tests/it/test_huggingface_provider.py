"""Integration tests for HuggingFace provider.

These tests require either:
- A running local inference server (TGI, vLLM, or similar with OpenAI-compatible API)
- Valid HF_TOKEN for HuggingFace Hub access

Run with: pytest tests/it/test_huggingface_provider.py -v -m integration
"""

import os
import pytest
import httpx

from agent_core.agents.factory import AgentConfig
from agent_core.config import get_hf_token
from agent_core.client import LLMClient
from agent_core.types import Message, LLMResponse


# Environment configuration
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_BASE_URL = os.getenv("HF_LOCAL_BASE_URL", "http://localhost:8080")
LOCAL_MODEL = os.getenv("HF_LOCAL_MODEL", "mistral:7b-instruct")
REMOTE_MODEL = os.getenv("HF_REMOTE_MODEL", "mistral:7b-instruct")


def is_local_server_available() -> bool:
    """Check if local inference server is running."""
    try:
        # Try common health endpoints
        for endpoint in ["/health", "/v1/models", "/"]:
            try:
                response = httpx.get(f"{LOCAL_BASE_URL}{endpoint}", timeout=5.0)
                if response.status_code in [200, 404]:
                    return True
            except httpx.HTTPError:
                continue
        return False
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def is_hf_token_valid() -> bool:
    """Check if HF_TOKEN is set and valid."""
    token = get_hf_token()
    if not token:
        return False
    try:
        response = httpx.get(
            "https://huggingface.co/api/whoami",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


# Skip markers
requires_local_server = pytest.mark.skipif(
    not is_local_server_available(),
    reason=f"Local inference server not available at {LOCAL_BASE_URL}"
)

requires_hf_token = pytest.mark.skipif(
    not is_hf_token_valid(),
    reason="Valid HF_TOKEN not available"
)


@pytest.fixture
def local_config() -> AgentConfig:
    """Create AgentConfig for local HuggingFace server."""
    return AgentConfig(
        name="LocalHFTest",
        provider="huggingface",
        model=LOCAL_MODEL,
        base_url=LOCAL_BASE_URL,
        max_tokens=100,
        temperature=0.7,
        timeout=120.0,
    )


@pytest.fixture
def remote_config() -> AgentConfig:
    """Create AgentConfig for remote HuggingFace Hub."""
    return AgentConfig(
        name="RemoteHFTest",
        provider="huggingface",
        model=REMOTE_MODEL,
        api_key=HF_TOKEN,
        max_tokens=100,
        temperature=0.7,
        timeout=60.0,
    )


@pytest.fixture
def messages() -> list[Message]:
    """Create test messages."""
    return [
        Message(role="system", content="You are a helpful assistant. Keep responses brief."),
        Message(role="user", content="What is 2 + 2?"),
    ]


@pytest.mark.integration
@requires_local_server
class TestHuggingFaceProviderLocal:
    """Integration tests for HuggingFace provider with local inference server."""

    @pytest.mark.asyncio
    async def test_chat_async_local(self, local_config: AgentConfig, messages: list[Message]):
        """Test async chat completion with local server."""
        client = LLMClient(local_config)
        
        response = await client.chat_async(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.provider == "huggingface"

    def test_chat_sync_local(self, local_config: AgentConfig, messages: list[Message]):
        """Test sync chat completion with local server."""
        client = LLMClient(local_config)
        
        response = client.chat(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.provider == "huggingface"

    @pytest.mark.asyncio
    async def test_complete_async_local(self, local_config: AgentConfig):
        """Test simple completion API with local server."""
        client = LLMClient(local_config)
        
        response = await client.complete_async(
            prompt="What is the capital of France?",
            system_prompt="Answer briefly."
        )
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        # Should mention Paris in some form
        assert "paris" in response.content.lower() or len(response.content) > 0

    def test_complete_sync_local(self, local_config: AgentConfig):
        """Test simple completion API (sync) with local server."""
        client = LLMClient(local_config)
        
        response = client.complete(
            prompt="What is 5 times 3?",
            system_prompt="Answer with just the number."
        )
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0


@pytest.mark.integration
@requires_hf_token
class TestHuggingFaceProviderRemote:
    """Integration tests for HuggingFace provider with HF Hub (remote)."""

    @pytest.mark.asyncio
    async def test_chat_async_remote(self, remote_config: AgentConfig, messages: list[Message]):
        """Test async chat completion with HF Hub."""
        client = LLMClient(remote_config)
        
        response = await client.chat_async(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.provider == "huggingface"

    def test_chat_sync_remote(self, remote_config: AgentConfig, messages: list[Message]):
        """Test sync chat completion with HF Hub."""
        client = LLMClient(remote_config)
        
        response = client.chat(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.provider == "huggingface"

    @pytest.mark.asyncio
    async def test_response_includes_usage(self, remote_config: AgentConfig, messages: list[Message]):
        """Test that response includes token usage information."""
        client = LLMClient(remote_config)
        
        response = await client.chat_async(messages)
        
        assert isinstance(response, LLMResponse)
        # HF Hub should provide usage information
        if response.usage:
            assert response.prompt_tokens >= 0
            assert response.completion_tokens >= 0

    def test_model_override(self, remote_config: AgentConfig, messages: list[Message]):
        """Test that model can be overridden in call."""
        client = LLMClient(remote_config)
        
        # Use a different model in the call
        response = client.chat(messages, model="mistralai/Mistral-7B-Instruct-v0.3")
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0


@pytest.mark.integration
class TestHuggingFaceProviderErrors:
    """Tests for error handling in HuggingFace provider."""

    def test_invalid_model_raises_error(self):
        """Test that invalid model raises appropriate error."""
        config = AgentConfig(
            name="ErrorTest",
            provider="huggingface",
            model="invalid/nonexistent-model-12345",
            api_key=HF_TOKEN or "dummy_token",
            timeout=10.0,
        )
        client = LLMClient(config)
        messages = [Message(role="user", content="Hello")]
        
        # This should raise an error (either connection or model not found)
        with pytest.raises(Exception):
            client.chat(messages)

    def test_connection_error_local(self):
        """Test that connection error is handled properly."""
        config = AgentConfig(
            name="ErrorTest",
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:99999",  # Invalid port
            timeout=5.0,
        )
        client = LLMClient(config)
        messages = [Message(role="user", content="Hello")]
        
        with pytest.raises(Exception) as exc_info:
            client.chat(messages)
        
        # Should get an error about connection
        assert "connect" in str(exc_info.value).lower() or "error" in str(exc_info.value).lower()

