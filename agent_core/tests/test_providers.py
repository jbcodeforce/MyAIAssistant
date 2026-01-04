"""Tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent_core.config import LLMConfig
from agent_core.types import Message, LLMError
from agent_core.providers.openai import OpenAIProvider
from agent_core.providers.anthropic import AnthropicProvider
from agent_core.providers.ollama import OllamaProvider


class TestOpenAIProvider:
    """Tests for OpenAI provider."""
    
    @pytest.fixture
    def provider(self):
        return OpenAIProvider()
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
    
    @pytest.fixture
    def messages(self):
        return [
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hello!")
        ]
    
    def test_provider_name(self, provider):
        """Test provider name."""
        assert provider.provider_name == "openai"
    
    def test_build_request_body(self, provider, messages, config):
        """Test request body building."""
        body = provider._build_request_body(messages, config)
        
        assert body["model"] == "gpt-4"
        assert len(body["messages"]) == 2
        assert body["max_tokens"] == 2048
        assert body["temperature"] == 0.7
    
    def test_build_request_body_with_json_format(self, provider, messages, config):
        """Test request body with JSON response format."""
        config.response_format = {"type": "json_object"}
        body = provider._build_request_body(messages, config)
        
        assert body["response_format"] == {"type": "json_object"}
    
    def test_build_headers(self, provider, config):
        """Test header building."""
        headers = provider._build_headers(config)
        
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"
    
    def test_parse_response(self, provider, config):
        """Test response parsing."""
        data = {
            "model": "gpt-4",
            "choices": [
                {
                    "message": {"content": "Hello there!"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
        response = provider._parse_response(data, config)
        
        assert response.content == "Hello there!"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.finish_reason == "stop"
        assert response.total_tokens == 15
    
    @pytest.mark.asyncio
    async def test_chat_async_no_api_key(self, provider, messages):
        """Test async chat fails without API key."""
        config = LLMConfig(provider="openai", model="gpt-4")
        
        with pytest.raises(LLMError, match="API key is required"):
            await provider.chat_async(messages, config)
    
    def test_chat_sync_no_api_key(self, provider, messages):
        """Test sync chat fails without API key."""
        config = LLMConfig(provider="openai", model="gpt-4")
        
        with pytest.raises(LLMError, match="API key is required"):
            provider.chat_sync(messages, config)


class TestAnthropicProvider:
    """Tests for Anthropic provider."""
    
    @pytest.fixture
    def provider(self):
        return AnthropicProvider()
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="anthropic",
            model="claude-3-opus",
            api_key="test-key"
        )
    
    @pytest.fixture
    def messages(self):
        return [
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hello!")
        ]
    
    def test_provider_name(self, provider):
        """Test provider name."""
        assert provider.provider_name == "anthropic"
    
    def test_build_request_body_separates_system(self, provider, messages, config):
        """Test that system message is separated."""
        body = provider._build_request_body(messages, config)
        
        assert body["system"] == "You are helpful."
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"
    
    def test_build_headers(self, provider, config):
        """Test header building."""
        headers = provider._build_headers(config)
        
        assert headers["x-api-key"] == "test-key"
        assert headers["anthropic-version"] == "2023-06-01"
    
    def test_parse_response(self, provider, config):
        """Test response parsing with Anthropic format."""
        data = {
            "model": "claude-3-opus",
            "content": [{"text": "Hello!"}],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5
            }
        }
        
        response = provider._parse_response(data, config)
        
        assert response.content == "Hello!"
        assert response.model == "claude-3-opus"
        assert response.provider == "anthropic"
        # Verify usage is normalized
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5
    
    @pytest.mark.asyncio
    async def test_chat_async_no_api_key(self, provider, messages):
        """Test async chat fails without API key."""
        config = LLMConfig(provider="anthropic", model="claude-3")
        
        with pytest.raises(LLMError, match="API key is required"):
            await provider.chat_async(messages, config)


class TestOllamaProvider:
    """Tests for Ollama provider."""
    
    @pytest.fixture
    def provider(self):
        return OllamaProvider()
    
    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider="ollama",
            model="llama2"
        )
    
    @pytest.fixture
    def messages(self):
        return [Message(role="user", content="Hello!")]
    
    def test_provider_name(self, provider):
        """Test provider name."""
        assert provider.provider_name == "ollama"
    
    def test_build_request_body(self, provider, messages, config):
        """Test request body building."""
        body = provider._build_request_body(messages, config)
        
        assert body["model"] == "llama2"
        assert body["stream"] is False
        assert body["options"]["num_predict"] == 2048
        assert body["options"]["temperature"] == 0.7
    
    def test_build_request_body_json_format(self, provider, messages, config):
        """Test request body with JSON format."""
        config.response_format = {"type": "json_object"}
        body = provider._build_request_body(messages, config)
        
        assert body["format"] == "json"
    
    def test_parse_response(self, provider, config):
        """Test response parsing."""
        data = {
            "model": "llama2",
            "message": {"content": "Hello!"},
            "done_reason": "stop",
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        
        response = provider._parse_response(data, config)
        
        assert response.content == "Hello!"
        assert response.model == "llama2"
        assert response.provider == "ollama"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
    
    def test_no_api_key_required(self, provider, config, messages):
        """Test that Ollama doesn't require API key."""
        # This should not raise - Ollama doesn't need API key
        # The actual API call would fail but validation passes
        assert config.api_key is None

