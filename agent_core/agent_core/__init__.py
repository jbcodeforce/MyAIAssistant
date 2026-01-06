"""Agent Core - Library for building agentic AI applications.

This library provides:
- Unified LLM client interface with sync/async support via HuggingFace InferenceClient
- Agent framework for building specialized agents
- Query classification and intelligent routing

Supported Backends:
    - HuggingFace Hub (remote models)
    - Local inference servers (TGI, vLLM, Ollama, etc.)

Example - LLM Client with local server:
    from agent_core import LLMClient, LLMConfig, Message
    
    config = LLMConfig(
        provider="huggingface",
        model="llama3",
        base_url="http://localhost:8080"
    )
    
    client = LLMClient(config)
    response = await client.chat_async([
        Message(role="user", content="Hello!")
    ])

Example - LLM Client with HuggingFace Hub:
    from agent_core import LLMClient, LLMConfig, Message
    import os
    
    config = LLMConfig(
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

from agent_core.config import LLMConfig, ProviderType, get_hf_token
from agent_core.types import Message, LLMResponse, LLMError, MessageRole
from agent_core.client import LLMClient
from agent_core.providers import (
    LLMProvider,
    HuggingFaceProvider,
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
