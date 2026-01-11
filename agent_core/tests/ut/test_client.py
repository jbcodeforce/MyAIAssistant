"""Tests for LLM Client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent_core.client import LLMClient
from agent_core.agents.factory import AgentConfig
from agent_core.types import Message, LLMResponse, LLMError
from agent_core.providers.base import LLMProvider


class TestLLMClient:
    """Tests for LLMClient class."""
    
    @pytest.fixture
    def hf_config_remote(self):
        """Create HuggingFace remote config for testing."""
        return AgentConfig(
            name="TestAgent",
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_test_token"
        )
    
    @pytest.fixture
    def hf_config_local(self):
        """Create HuggingFace local config for testing."""
        return AgentConfig(
            name="TestAgent",
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080"
        )
    
    def test_create_client(self, hf_config_remote):
        """Test creating an LLM client."""
        client = LLMClient(hf_config_remote)
        
        assert client.config == hf_config_remote
        assert client._provider is None  # Lazy initialization
    
    def test_provider_lazy_initialization(self, hf_config_remote):
        """Test that provider is lazily initialized."""
        client = LLMClient(hf_config_remote)
        
        # Provider not created yet
        assert client._provider is None
        
        # Access provider property
        provider = client.provider
        
        # Now it's created
        assert client._provider is not None
        assert provider.provider_name == "huggingface"
    
    def test_provider_cached(self, hf_config_remote):
        """Test that provider is cached."""
        client = LLMClient(hf_config_remote)
        
        provider1 = client.provider
        provider2 = client.provider
        
        assert provider1 is provider2
    
    def test_unsupported_provider(self):
        """Test error for unsupported provider."""
        config = AgentConfig(
            name="TestAgent",
            provider="unsupported",
            model="model"
        )
        client = LLMClient(config)
        
        with pytest.raises(LLMError, match="Unsupported provider"):
            _ = client.provider
    
    @pytest.mark.asyncio
    async def test_chat_async(self, hf_config_remote):
        """Test async chat method."""
        client = LLMClient(hf_config_remote)
        
        mock_response = LLMResponse(
            content="Hello!",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            provider="huggingface"
        )
        
        mock_provider = MagicMock()
        mock_provider.chat_async = AsyncMock(return_value=mock_response)
        client._provider = mock_provider
        
        messages = [Message(role="user", content="Hi")]
        response = await client.chat_async(messages)
        
        assert response.content == "Hello!"
        mock_provider.chat_async.assert_called_once()
    
    def test_chat_sync(self, hf_config_remote):
        """Test sync chat method."""
        client = LLMClient(hf_config_remote)
        
        mock_response = LLMResponse(
            content="Hello!",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            provider="huggingface"
        )
        
        mock_provider = MagicMock()
        mock_provider.chat_sync = MagicMock(return_value=mock_response)
        client._provider = mock_provider
        
        messages = [Message(role="user", content="Hi")]
        response = client.chat(messages)
        
        assert response.content == "Hello!"
        mock_provider.chat_sync.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_async(self, hf_config_remote):
        """Test async complete method."""
        client = LLMClient(hf_config_remote)
        
        mock_response = LLMResponse(
            content="Response",
            model="llama3",
            provider="huggingface"
        )
        
        with patch.object(client, 'chat_async', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            response = await client.complete_async("Tell me a joke")
            
            assert response.content == "Response"
            # Verify message was created correctly
            call_args = mock_chat.call_args[0][0]
            assert len(call_args) == 1
            assert call_args[0].role == "user"
            assert call_args[0].content == "Tell me a joke"
    
    @pytest.mark.asyncio
    async def test_complete_async_with_system(self, hf_config_remote):
        """Test async complete with system prompt."""
        client = LLMClient(hf_config_remote)
        
        mock_response = LLMResponse(
            content="Response",
            model="llama3",
            provider="huggingface"
        )
        
        with patch.object(client, 'chat_async', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            await client.complete_async(
                "Hello",
                system_prompt="You are helpful."
            )
            
            call_args = mock_chat.call_args[0][0]
            assert len(call_args) == 2
            assert call_args[0].role == "system"
            assert call_args[1].role == "user"
    
    def test_complete_sync(self, hf_config_remote):
        """Test sync complete method."""
        client = LLMClient(hf_config_remote)
        
        mock_response = LLMResponse(
            content="Response",
            model="llama3",
            provider="huggingface"
        )
        
        with patch.object(client, 'chat') as mock_chat:
            mock_chat.return_value = mock_response
            
            response = client.complete("Tell me a joke")
            
            assert response.content == "Response"
    
    def test_merge_config_no_overrides(self, hf_config_remote):
        """Test config merge with no overrides."""
        client = LLMClient(hf_config_remote)
        
        merged = client._merge_config({})
        
        assert merged is hf_config_remote
    
    def test_merge_config_with_overrides(self, hf_config_remote):
        """Test config merge with overrides."""
        client = LLMClient(hf_config_remote)
        
        merged = client._merge_config({
            "temperature": 0.5,
            "max_tokens": 1000
        })
        
        assert merged.temperature == 0.5
        assert merged.max_tokens == 1000
        # Other values unchanged
        assert merged.provider == "huggingface"
        assert merged.model == "meta-llama/Meta-Llama-3-8B-Instruct"
    
    @pytest.mark.asyncio
    async def test_chat_with_overrides(self, hf_config_remote):
        """Test chat with config overrides."""
        client = LLMClient(hf_config_remote)
        
        mock_response = LLMResponse(
            content="Response",
            model="llama3",
            provider="huggingface"
        )
        
        mock_provider = MagicMock()
        mock_provider.chat_async = AsyncMock(return_value=mock_response)
        client._provider = mock_provider
        
        await client.chat_async(
            [Message(role="user", content="Hi")],
            temperature=0.1
        )
        
        # Verify merged config was passed
        call_args = mock_provider.chat_async.call_args
        config = call_args[0][1]
        assert config.temperature == 0.1


class TestLLMClientProviderRegistration:
    """Tests for custom provider registration."""
    
    def test_register_custom_provider(self):
        """Test registering a custom provider."""
        class CustomProvider(LLMProvider):
            provider_name = "custom"
            
            async def chat_async(self, messages, config):
                pass
            
            def chat_sync(self, messages, config):
                pass
        
        LLMClient.register_provider("custom", CustomProvider)
        
        assert "custom" in LLMClient.PROVIDERS
        assert LLMClient.PROVIDERS["custom"] == CustomProvider
        
        # Clean up
        del LLMClient.PROVIDERS["custom"]


class TestLLMClientHuggingFaceProvider:
    """Tests to verify HuggingFace provider works with client."""
    
    def test_huggingface_provider_creation_remote(self):
        """Test HuggingFace provider is created correctly for remote."""
        config = AgentConfig(
            name="TestAgent",
            provider="huggingface",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_test_token"
        )
        client = LLMClient(config)
        
        assert client.provider.provider_name == "huggingface"
    
    def test_huggingface_provider_creation_local(self):
        """Test HuggingFace provider is created correctly for local."""
        config = AgentConfig(
            name="TestAgent",
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080"
        )
        client = LLMClient(config)
        
        assert client.provider.provider_name == "huggingface"
