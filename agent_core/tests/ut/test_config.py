"""Tests for LLM configuration."""

import pytest

from agent_core.config import LLMConfig, DEFAULT_BASE_URLS


class TestLLMConfig:
    """Tests for LLMConfig dataclass."""
    
    def test_create_config(self):
        """Test creating a configuration."""
        config = LLMConfig(
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_test_token"
        )
        
        assert config.provider == "huggingface"
        assert config.model == "meta-llama/Meta-Llama-3-8B-Instruct"
        assert config.api_key == "hf_test_token"
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080"
        )
        
        assert config.max_tokens == 2048
        assert config.temperature == 0.7
        assert config.timeout == 60.0
        assert config.response_format is None
    
    def test_get_base_url_custom(self):
        """Test getting custom base URL."""
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080"
        )
        
        assert config.get_base_url() == "http://localhost:8080"
    
    def test_get_base_url_default_is_none(self):
        """Test getting default base URL for HuggingFace (None for HF Hub)."""
        config = LLMConfig(
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_test_token"
        )
        
        assert config.get_base_url() is None
    
    def test_validate_valid_config_remote(self):
        """Test validating a valid remote configuration."""
        config = LLMConfig(
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_test_token"
        )
        
        # Should not raise
        config.validate()
    
    def test_validate_valid_config_local(self):
        """Test validating a valid local configuration."""
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080"
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
            provider="huggingface",
            model="",
            base_url="http://localhost:8080"
        )
        
        with pytest.raises(ValueError, match="Model name is required"):
            config.validate()
    
    def test_validate_huggingface_remote_requires_token(self):
        """Test HuggingFace remote (no base_url) requires API key."""
        config = LLMConfig(
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct"
        )
        
        with pytest.raises(ValueError, match="HF_TOKEN is required"):
            config.validate()
    
    def test_validate_huggingface_remote_with_token(self):
        """Test HuggingFace remote with token passes validation."""
        config = LLMConfig(
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_test_token"
        )
        
        # Should not raise
        config.validate()
    
    def test_validate_huggingface_local_no_token_required(self):
        """Test HuggingFace local (with base_url) doesn't require token."""
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080"
        )
        
        # Should not raise - local server doesn't need token
        config.validate()
    
    def test_validate_invalid_temperature(self):
        """Test validation fails for invalid temperature."""
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080",
            temperature=-0.1
        )
        
        with pytest.raises(ValueError, match="Temperature must be"):
            config.validate()
        
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080",
            temperature=2.5
        )
        
        with pytest.raises(ValueError, match="Temperature must be"):
            config.validate()
    
    def test_validate_invalid_max_tokens(self):
        """Test validation fails for invalid max_tokens."""
        config = LLMConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080",
            max_tokens=0
        )
        
        with pytest.raises(ValueError, match="max_tokens must be"):
            config.validate()


class TestDefaultBaseUrls:
    """Tests for default base URLs."""
    
    def test_huggingface_in_defaults(self):
        """Test that HuggingFace provider has default URL entry."""
        assert "huggingface" in DEFAULT_BASE_URLS
    
    def test_huggingface_default_is_none(self):
        """Test HuggingFace default base URL is None (uses HF Hub)."""
        assert DEFAULT_BASE_URLS["huggingface"] is None
