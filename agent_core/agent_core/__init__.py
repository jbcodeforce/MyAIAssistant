"""Agent Core - Library for building agentic AI applications.

This library provides:
- Unified LLM client interface with sync/async support
- Agent framework for building specialized agents
- Query classification and intelligent routing

Supported LLM Providers:
    - OpenAI (GPT-4, GPT-3.5, etc.)
    - Anthropic (Claude models)
    - Ollama (local models)

Example - LLM Client:
    from agent_core import LLMClient, LLMConfig, Message
    
    config = LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key="your-key"
    )
    
    client = LLMClient(config)
    response = await client.chat_async([
        Message(role="user", content="Hello!")
    ])

Example - Agent Framework:
    from agent_core import BaseAgent, AgentResponse, QueryClassifier, AgentRouter
    
    class MyAgent(BaseAgent):
        agent_type = "my_agent"
        
        async def execute(self, query, conversation_history=None, context=None):
            # Implementation
            pass
        
        def build_system_prompt(self, context=None):
            return "You are a helpful assistant."
"""

from agent_core.config import LLMConfig, ProviderType
from agent_core.types import Message, LLMResponse, LLMError, MessageRole
from agent_core.client import LLMClient
from agent_core.providers import (
    LLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
)
from agent_core.agents import (
    # Base agent
    BaseAgent,
    AgentResponse,
    # Query classification
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
    CLASSIFICATION_PROMPT,
    # Agent routing
    AgentRouter,
    WorkflowState,
    RoutedResponse,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "LLMClient",
    # Configuration
    "LLMConfig",
    "ProviderType",
    # Types
    "Message",
    "MessageRole",
    "LLMResponse",
    "LLMError",
    # Providers
    "LLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    # Agent framework
    "BaseAgent",
    "AgentResponse",
    # Query classification
    "QueryClassifier",
    "QueryIntent",
    "ClassificationResult",
    "CLASSIFICATION_PROMPT",
    # Agent routing
    "AgentRouter",
    "WorkflowState",
    "RoutedResponse",
]

