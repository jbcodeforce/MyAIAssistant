"""LLM Client - unified interface for multiple LLM providers."""

from typing import Optional

from agent_core.config import LLMConfig
from agent_core.types import Message, LLMResponse, LLMError
from agent_core.providers.base import LLMProvider
from agent_core.providers.openai import OpenAIProvider
from agent_core.providers.anthropic import AnthropicProvider
from agent_core.providers.ollama import OllamaProvider


class LLMClient:
    """
    Unified LLM client with support for multiple providers.
    
    Provides both synchronous and asynchronous APIs for chat completions.
    
    Example:
        config = LLMConfig(provider="openai", model="gpt-4", api_key="...")
        client = LLMClient(config)
        
        # Async usage
        response = await client.chat_async([Message(role="user", content="Hello")])
        
        # Sync usage
        response = client.chat([Message(role="user", content="Hello")])
    """
    
    PROVIDERS: dict[str, type[LLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM client.
        
        Args:
            config: LLM configuration specifying provider, model, etc.
        """
        self.config = config
        self._provider: Optional[LLMProvider] = None
    
    @property
    def provider(self) -> LLMProvider:
        """Get the provider instance, creating it if necessary."""
        if self._provider is None:
            provider_class = self.PROVIDERS.get(self.config.provider)
            if provider_class is None:
                raise LLMError(
                    message=f"Unsupported provider: {self.config.provider}",
                    provider=self.config.provider,
                )
            self._provider = provider_class()
        return self._provider
    
    async def chat_async(
        self,
        messages: list[Message],
        **kwargs
    ) -> LLMResponse:
        """
        Send a chat completion request asynchronously.
        
        Args:
            messages: List of chat messages
            **kwargs: Additional parameters to override config
            
        Returns:
            LLMResponse with the completion
        """
        config = self._merge_config(kwargs)
        return await self.provider.chat_async(messages, config)
    
    def chat(
        self,
        messages: list[Message],
        **kwargs
    ) -> LLMResponse:
        """
        Send a chat completion request synchronously.
        
        Args:
            messages: List of chat messages
            **kwargs: Additional parameters to override config
            
        Returns:
            LLMResponse with the completion
        """
        config = self._merge_config(kwargs)
        return self.provider.chat_sync(messages, config)
    
    async def complete_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Simple completion API - wraps prompt in messages format.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters to override config
            
        Returns:
            LLMResponse with the completion
        """
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))
        
        return await self.chat_async(messages, **kwargs)
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Simple completion API (sync) - wraps prompt in messages format.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters to override config
            
        Returns:
            LLMResponse with the completion
        """
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=prompt))
        
        return self.chat(messages, **kwargs)
    
    def _merge_config(self, overrides: dict) -> LLMConfig:
        """Merge config overrides with base config."""
        if not overrides:
            return self.config
        
        # Create new config with overrides
        return LLMConfig(
            provider=overrides.get("provider", self.config.provider),
            model=overrides.get("model", self.config.model),
            api_key=overrides.get("api_key", self.config.api_key),
            base_url=overrides.get("base_url", self.config.base_url),
            max_tokens=overrides.get("max_tokens", self.config.max_tokens),
            temperature=overrides.get("temperature", self.config.temperature),
            timeout=overrides.get("timeout", self.config.timeout),
            response_format=overrides.get("response_format", self.config.response_format),
        )
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type[LLMProvider]) -> None:
        """
        Register a custom provider.
        
        Args:
            name: Provider name
            provider_class: Provider class implementing LLMProvider
        """
        cls.PROVIDERS[name] = provider_class

