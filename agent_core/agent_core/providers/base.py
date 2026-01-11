"""Base provider protocol for LLM integrations."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_core.agents.factory import AgentConfig
    from agent_core.types import Message, LLMResponse


class LLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    Each provider implements the chat method for its specific API.
    """
    
    provider_name: str = "base"
    
    @abstractmethod
    async def chat_async(
        self,
        messages: list["Message"],
        config: "AgentConfig"
    ) -> "LLMResponse":
        """
        Send a chat completion request asynchronously.
        
        Args:
            messages: List of chat messages
            config: Agent configuration
            
        Returns:
            LLMResponse with the completion
        """
        pass
    
    @abstractmethod
    def chat_sync(
        self,
        messages: list["Message"],
        config: "AgentConfig"
    ) -> "LLMResponse":
        """
        Send a chat completion request synchronously.
        
        Args:
            messages: List of chat messages
            config: Agent configuration
            
        Returns:
            LLMResponse with the completion
        """
        pass
