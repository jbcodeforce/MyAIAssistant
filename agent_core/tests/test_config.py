"""Tests for LLM configuration."""

import pytest

from agent_core.config import LLMConfig, DEFAULT_BASE_URLS


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""
    
    def test_create_config(self):
        """Test creating a configuration."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "test-key"
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="key"
        )
        
        assert config.max_tokens == 2048
        assert config.temperature == 0.7
        assert config.timeout == 60.0
        assert config.base_url is None
        assert config.response_format is None
    
    def test_get_base_url_default(self):
        """Test getting default base URL."""
        config = LLMConfig(provider="openai", model="gpt-4", api_key="key")
        assert config.get_base_url() == "https://api.openai.com/v1"
        
        config = LLMConfig(provider="anthropic", model="claude-3", api_key="key")
        assert config.get_base_url() == "https://api.anthropic.com/v1"
        
        config = LLMConfig(provider="ollama", model="llama2")
        assert config.get_base_url() == "http://localhost:11434"
    
    def test_get_base_url_custom(self):
        """Test getting custom base URL."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="key",
            base_url="https://custom.api.com"
        )
        
        assert config.get_base_url() == "https://custom.api.com"
    
    def test_validate_valid_config(self):
        """Test validating a valid configuration."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        # Should not raise
        config.validate()
    
    def test_validate_unsupported_provider(self):
        """Test validation fails for unsupported provider."""
        config = LLMConfig(
            provider="unsupported",
            model="model"
        )
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            config.validate()
    
    def test_validate_missing_model(self):
        """Test validation fails for missing model."""
        config = LLMConfig(
            provider="openai",
            model="",
            api_key="key"
        )
        
        with pytest.raises(ValueError, match="Model name is required"):
            config.validate()
    
    def test_validate_missing_api_key_openai(self):
        """Test validation fails for missing API key with OpenAI."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4"
        )
        
        with pytest.raises(ValueError, match="API key is required"):
            config.validate()
    
    def test_validate_missing_api_key_anthropic(self):
        """Test validation fails for missing API key with Anthropic."""
        config = LLMConfig(
            provider="anthropic",
            model="claude-3"
        )
        
        with pytest.raises(ValueError, match="API key is required"):
            config.validate()
    
    def test_validate_ollama_no_api_key_required(self):
        """Test Ollama doesn't require API key."""
        config = LLMConfig(
            provider="ollama",
            model="llama2"
        )
        
        # Should not raise
        config.validate()
    
    def test_validate_invalid_temperature(self):
        """Test validation fails for invalid temperature."""
        config = LLMConfig(
            provider="ollama",
            model="llama2",
            temperature=-0.1
        )
        
        with pytest.raises(ValueError, match="Temperature must be"):
            config.validate()
        
        config = LLMConfig(
            provider="ollama",
            model="llama2",
            temperature=2.5
        )
        
        with pytest.raises(ValueError, match="Temperature must be"):
            config.validate()
    
    def test_validate_invalid_max_tokens(self):
        """Test validation fails for invalid max_tokens."""
        config = LLMConfig(
            provider="ollama",
            model="llama2",
            max_tokens=0
        )
        
        with pytest.raises(ValueError, match="max_tokens must be"):
            config.validate()


class TestDefaultBaseUrls:
    """Tests for default base URLs."""
    
    def test_all_providers_have_defaults(self):
        """Test that all supported providers have default URLs."""
        assert "openai" in DEFAULT_BASE_URLS
        assert "anthropic" in DEFAULT_BASE_URLS
        assert "ollama" in DEFAULT_BASE_URLS

