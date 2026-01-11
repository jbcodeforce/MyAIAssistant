"""Agent Core - Library for building agentic AI applications.

This library provides:
- Unified LLM client interface with sync/async support via HuggingFace InferenceClient
- Agent framework for building specialized agents
- Query classification and intelligent routing

Supported Backends:
    - HuggingFace Hub (remote models)
    - Local inference servers (TGI, vLLM, Ollama, etc.)

Example - LLM Client with local server:
    from agent_core import LLMClient, AgentConfig, Message
    
    config = AgentConfig(
        provider="huggingface",
        model="llama3",
        base_url="http://localhost:8080"
    )
    
    client = LLMClient(config)
    response = await client.chat_async([
        Message(role="user", content="Hello!")
    ])

Example - LLM Client with HuggingFace Hub:
    from agent_core import LLMClient, AgentConfig, Message
    import os
    
    config = AgentConfig(
        provider="huggingface",
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        api_key=os.getenv("HF_TOKEN")
    )
    
    client = LLMClient(config)
    response = client.chat([
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

from agent_core.config import ProviderType, get_hf_token
from agent_core.types import Message, LLMResponse, LLMError, MessageRole
from agent_core.client import LLMClient
from agent_core.providers import (
    LLMProvider,
    HuggingFaceProvider,
)
from agent_core.agents import (
    # Base agent and types
    BaseAgent,
    AgentResponse,
    AgentInput,
    # Agent factory and config
    AgentFactory,
    AgentConfig,
    get_agent_factory,
    reset_agent_factory,
    # Query classification
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
    CLASSIFICATION_PROMPT,
    # Agent routing
    AgentRouter,
    WorkflowState,
    RoutedResponse,
    get_agent_router,
    reset_agent_router,
)

__version__ = "0.1.0"

__all__ = [
    # Main client
    "LLMClient",
    # Configuration
    "AgentConfig",
    "ProviderType",
    "get_hf_token",
    # Types
    "Message",
    "MessageRole",
    "LLMResponse",
    "LLMError",
    # Providers
    "LLMProvider",
    "HuggingFaceProvider",
    # Agent framework
    "BaseAgent",
    "AgentResponse",
    "AgentInput",
    # Agent factory
    "AgentFactory",
    "get_agent_factory",
    "reset_agent_factory",
    # Query classification
    "QueryClassifier",
    "QueryIntent",
    "ClassificationResult",
    "CLASSIFICATION_PROMPT",
    # Agent routing
    "AgentRouter",
    "WorkflowState",
    "RoutedResponse",
    "get_agent_router",
    "reset_agent_router",
]
