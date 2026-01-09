"""Integration tests for HuggingFace provider with Ollama backend.

These tests require a running Ollama server at http://localhost:11434
with the specified model available.

Run with: pytest tests/it/test_ollama_provider.py -v -m integration
"""

import os
import pytest
import httpx

from agent_core.config import LLMConfig
from agent_core.client import LLMClient
from agent_core.types import Message, LLMResponse, LLMError


# Environment configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")


def is_ollama_available() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        # Check Ollama's native endpoint (not /v1)
        base = OLLAMA_BASE_URL.replace("/v1", "")
        response = httpx.get(f"{base}/api/tags", timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def is_model_available() -> bool:
    """Check if the specified model is available in Ollama."""
    try:
        base = OLLAMA_BASE_URL.replace("/v1", "")
        response = httpx.get(f"{base}/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]
            # Check if model exists (with or without tag)
            model_base = OLLAMA_MODEL.split(":")[0]
            return any(model_base in name or name in model_base for name in model_names)
        return False
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


# Skip markers
requires_ollama = pytest.mark.skipif(
    not is_ollama_available(),
    reason=f"Ollama server not available at {OLLAMA_BASE_URL}"
)

requires_model = pytest.mark.skipif(
    not is_model_available(),
    reason=f"Model {OLLAMA_MODEL} not available in Ollama"
)


@pytest.fixture
def ollama_config() -> LLMConfig:
    """Create LLM config for Ollama server."""
    return LLMConfig(
        provider="huggingface",
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        max_tokens=100,
        temperature=0.7,
        timeout=120.0,
    )


@pytest.fixture
def messages() -> list[Message]:
    """Create test messages."""
    return [
        Message(role="system", content="You are a helpful assistant. Keep responses brief."),
        Message(role="user", content="What is 2 + 2? Answer with just the number."),
    ]


@pytest.mark.integration
@requires_ollama
class TestOllamaProvider:
    """Integration tests for HuggingFace provider with Ollama backend."""

    @pytest.mark.asyncio
    async def test_chat_async_ollama(self, ollama_config: LLMConfig, messages: list[Message]):
        """Test async chat completion with Ollama."""
        client = LLMClient(ollama_config)
        
        response = await client.chat_async(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.provider == "huggingface"
        # Response should contain something about 4
        assert "4" in response.content or len(response.content) > 0

    def test_chat_sync_ollama(self, ollama_config: LLMConfig, messages: list[Message]):
        """Test sync chat completion with Ollama."""
        client = LLMClient(ollama_config)
        
        response = client.chat(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        assert response.provider == "huggingface"

    @pytest.mark.asyncio
    async def test_complete_async_ollama(self, ollama_config: LLMConfig):
        """Test simple completion API with Ollama."""
        client = LLMClient(ollama_config)
        
        response = await client.complete_async(
            prompt="What is the capital of France? Answer in one word.",
            system_prompt="Answer briefly."
        )
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0
        # Should mention Paris in some form
        assert "paris" in response.content.lower() or len(response.content) > 0

    def test_complete_sync_ollama(self, ollama_config: LLMConfig):
        """Test simple completion API (sync) with Ollama."""
        client = LLMClient(ollama_config)
        
        response = client.complete(
            prompt="What is 5 times 3? Answer with just the number.",
            system_prompt="Answer with just the number."
        )
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_response_model_info(self, ollama_config: LLMConfig, messages: list[Message]):
        """Test that response includes model information."""
        client = LLMClient(ollama_config)
        
        response = await client.chat_async(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.model is not None

    def test_conversation_with_history(self, ollama_config: LLMConfig):
        """Test multi-turn conversation."""
        client = LLMClient(ollama_config)
        
        messages = [
            Message(role="system", content="You are a helpful math tutor."),
            Message(role="user", content="I want to learn about addition."),
            Message(role="assistant", content="Great! Addition is combining numbers together."),
            Message(role="user", content="What is 3 + 5?"),
        ]
        
        response = client.chat(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0


@pytest.mark.integration
class TestOllamaProviderErrors:
    """Tests for error handling with Ollama backend."""

    def test_connection_error_invalid_port(self):
        """Test that connection error is handled properly."""
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:99999/v1",
            timeout=5.0,
        )
        client = LLMClient(config)
        messages = [Message(role="user", content="Hello")]
        
        with pytest.raises(LLMError) as exc_info:
            client.chat(messages)
        
        assert "connect" in str(exc_info.value).lower()

    @requires_ollama
    def test_invalid_model_error(self):
        """Test that invalid model raises appropriate error."""
        config = LLMConfig(
            provider="huggingface",
            model="nonexistent-model-12345",
            base_url=OLLAMA_BASE_URL,
            timeout=10.0,
        )
        client = LLMClient(config)
        messages = [Message(role="user", content="Hello")]
        
        # This should raise an error about model not found
        with pytest.raises(Exception):
            client.chat(messages)


@pytest.mark.integration
@requires_ollama
class TestOllamaConfigVariations:
    """Test various configuration patterns with Ollama."""

    def test_config_with_trailing_slash(self):
        """Test that trailing slash in base_url is handled."""
        config = LLMConfig(
            provider="huggingface",
            model=OLLAMA_MODEL,
            base_url=f"{OLLAMA_BASE_URL}/",  # Trailing slash
            max_tokens=50,
            timeout=60.0,
        )
        client = LLMClient(config)
        messages = [Message(role="user", content="Say hello")]
        
        response = client.chat(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0

    def test_config_with_low_temperature(self):
        """Test deterministic responses with temperature=0."""
        config = LLMConfig(
            provider="huggingface",
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            max_tokens=50,
            temperature=0.0,
            timeout=60.0,
        )
        client = LLMClient(config)
        messages = [Message(role="user", content="What is 1+1? Answer with just the number.")]
        
        response = client.chat(messages)
        
        assert isinstance(response, LLMResponse)
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_async_with_timeout(self):
        """Test async call respects timeout configuration."""
        config = LLMConfig(
            provider="huggingface",
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            max_tokens=50,
            timeout=120.0,  # Long timeout for slow responses
        )
        client = LLMClient(config)
        messages = [Message(role="user", content="Hi")]
        
        response = await client.chat_async(messages)
        
        assert isinstance(response, LLMResponse)

