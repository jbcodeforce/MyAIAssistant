"""Base agent interface and shared utilities.

This module provides the abstract base class for specialized agents
in agentic AI applications.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from agent_core.client import LLMClient
from agent_core.config import LLMConfig
from agent_core.types import Message as LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from an agent execution."""
    message: str
    context_used: list[dict] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    agent_type: str = ""
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for specialized agents.
    
    Each agent handles a specific type of query intent.
    Uses LLMClient for LLM integration.
    
    Example:
        class MyAgent(BaseAgent):
            agent_type = "my_agent"
            
            async def execute(self, query, conversation_history=None, context=None):
                messages = [{"role": "user", "content": query}]
                response = await self._call_llm(messages)
                return AgentResponse(message=response, agent_type=self.agent_type)
            
            def build_system_prompt(self, context=None):
                return "You are a helpful assistant."
    """
    
    agent_type: str = "base"
    
    def __init__(
        self,
        llm_config: LLMConfig = None,
        llm_client: LLMClient = None,
        # Convenience parameters for creating config
        provider: str = None,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ):
        """
        Initialize the agent with LLM configuration.
        
        Args:
            llm_config: Pre-built LLM configuration (takes precedence)
            llm_client: Pre-built LLM client (takes precedence over config)
            provider: LLM provider name (openai, anthropic, ollama)
            model: Model name
            api_key: API key for the provider
            base_url: Custom base URL for the API
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        """
        if llm_client:
            self._llm_client = llm_client
            self._llm_config = llm_client.config
        elif llm_config:
            self._llm_config = llm_config
            self._llm_client = LLMClient(llm_config)
        else:
            # Build config from individual parameters
            self._llm_config = LLMConfig(
                provider=provider or "ollama",
                model=model or "llama2",
                api_key=api_key,
                base_url=base_url,
                max_tokens=max_tokens,
                temperature=temperature
            )
            self._llm_client = LLMClient(self._llm_config)
        
        # Expose config values for convenience
        self.provider = self._llm_config.provider
        self.model = self._llm_config.model

    @abstractmethod
    async def execute(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None
    ) -> AgentResponse:
        """
        Execute the agent with the given query.
        
        Args:
            query: User's input query
            conversation_history: Previous messages in conversation
            context: Additional context (entities, metadata, etc.)
            
        Returns:
            AgentResponse with the result
        """
        pass

    @abstractmethod
    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """Build the system prompt for this agent."""
        pass

    async def _call_llm(self, messages: list[dict]) -> str:
        """
        Call the LLM using the configured client.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            The LLM response content as a string
        """
        # Convert dict messages to LLMMessage objects
        llm_messages = [
            LLMMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
        
        response: LLMResponse = await self._llm_client.chat_async(llm_messages)
        return response.content

    def _call_llm_sync(self, messages: list[dict]) -> str:
        """
        Call the LLM synchronously.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            The LLM response content as a string
        """
        llm_messages = [
            LLMMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]
        
        response: LLMResponse = self._llm_client.chat(llm_messages)
        return response.content

