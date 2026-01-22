"""Tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent_core.agents.factory import AgentConfig
from agent_core.types import Message, LLMError
from agent_core.providers.huggingface import HuggingFaceProvider


class TestHuggingFaceProvider:
    """Tests for HuggingFace provider."""
    
    @pytest.fixture
    def provider(self):
        return HuggingFaceProvider()
    
    @pytest.fixture
    def config_remote(self):
        """Config for remote HF Hub model."""
        return AgentConfig(
            name="TestAgent",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_test_token"
        )
    
    @pytest.fixture
    def config_local(self):
        """Config for local inference server."""
        return AgentConfig(
            name="TestAgent",
            model="llama3",
            base_url="http://localhost:8080"
        )
    
    @pytest.fixture
    def messages(self):
        return [
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hello!")
        ]
    
    def test_get_token_from_config(self, provider, config_remote):
        """Test token retrieval from config."""
        token = provider._get_token(config_remote)
        assert token == "hf_test_token"
    
    def test_get_token_from_env(self, provider, config_local):
        """Test token retrieval falls back to environment."""
        with patch("agent_core.providers.huggingface.get_hf_token", return_value="hf_env_token"):
            token = provider._get_token(config_local)
            assert token == "hf_env_token"
    
    def test_is_local_server_remote(self, provider, config_remote):
        """Test is_local_server returns False for remote HF Hub."""
        assert provider._is_local_server(config_remote) is False
    
    def test_is_local_server_local(self, provider, config_local):
        """Test is_local_server returns True for local server."""
        assert provider._is_local_server(config_local) is True
    
    def test_parse_response(self, provider, config_remote):
        """Test response parsing from HuggingFace ChatCompletionOutput."""
        # Create a mock response object
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello there!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "meta-llama/Meta-Llama-3-8B-Instruct"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.model_dump = MagicMock(return_value={})
        
        response = provider._parse_response(mock_response, config_remote)
        
        assert response.content == "Hello there!"
        assert response.model == "meta-llama/Meta-Llama-3-8B-Instruct"
        assert response.provider == "huggingface"
        assert response.finish_reason == "stop"
        assert response.total_tokens == 15
    
    def test_parse_response_no_usage(self, provider, config_remote):
        """Test response parsing when usage is not available."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "llama3"
        mock_response.usage = None
        mock_response.model_dump = MagicMock(return_value={})
        
        response = provider._parse_response(mock_response, config_remote)
        
        assert response.content == "Hello!"
        assert response.usage is None
    
    def test_handle_error(self, provider):
        """Test error handling."""
        error = Exception("Connection refused")
        
        with pytest.raises(LLMError) as exc_info:
            provider._handle_error(error)
        
        assert "Connection refused" in str(exc_info.value)
        assert exc_info.value.provider == "huggingface"
    
    def test_no_api_key_required_for_local(self, provider, config_local, messages):
        """Test that local server doesn't require API key."""
        # Local server with base_url doesn't require token
        assert config_local.api_key is None
        assert config_local.base_url is not None
