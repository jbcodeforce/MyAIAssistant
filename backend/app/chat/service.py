"""Chat service for LLM-powered task planning with RAG integration."""

import logging
import json
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from app.core.config import get_settings, resolve_agent_config_dir
from agent_core.agents.agent_factory import  AgentFactory, get_agent_factory
from agent_core.agents.base_agent import AgentInput
from agent_core.agents.query_classifier import QueryIntent
from agent_core.agents.agent_router import  RoutedResponse, AgentRouter

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A chat message."""
    role: str  # "user", "assistant", or "system"
    content: str


@dataclass
class ChatResponse:
    """Response from the chat service."""
    message: str
    context_used: list[dict]  # RAG context that was used
    # Optional routing metadata
    intent: Optional[str] = None
    agent_type: Optional[str] = None
    classification_confidence: Optional[float] = None


class ChatService:
    """
    Service for LLM-powered chat with RAG integration.
    
    Supports multiple providers: OpenAI, Anthropic, and Ollama.
    Uses agent_core.LLMClient for LLM integration.
    Now includes agent routing for intelligent query handling.
    """

    def __init__(
        self
    ):
        # Get agent config directory from settings
        settings = get_settings()
        config_dir = resolve_agent_config_dir(settings.agent_config_dir)
        
        # Initialize agent router with this config
        self._agent_router = AgentRouter(config_dir=config_dir)

    async def chat_with_todo(
        self,
        todo_title: str,
        todo_description: Optional[str],
        user_message: str,
        conversation_history: list[ChatMessage] = None,
        use_rag: bool = True
    ) -> ChatResponse:
        """
        Chat about a todo task, optionally using RAG for context.
        
        Args:
            todo_title: Title of the todo task
            todo_description: Optional description of the task
            user_message: The user's message/question
            conversation_history: Previous messages in the conversation
            use_rag: Whether to use RAG to retrieve relevant context
            
        Returns:
            ChatResponse with the assistant's reply and context used
        """
        # Get agent config directory from settings
        settings = get_settings()
        config_dir = resolve_agent_config_dir(settings.agent_config_dir)
        factory = get_agent_factory(config_dir=config_dir)
        agent = factory.create_agent("TaskAgent")
 
        context = {"task_title": todo_title, "task_description": todo_description}
        response = await agent.execute(AgentInput(query=user_message,use_rag=use_rag,conversation_history=conversation_history, context=context))
        
        return ChatResponse(
            message=response.content,
            context_used=context
        )

    async def chat_with_routing(
        self,
        user_message: str,
        conversation_history: list[ChatMessage] = None,
        context: dict = None,
        force_intent: QueryIntent = None
    ) -> ChatResponse:
        """
        Chat with intelligent query classification and agent routing.
        
        This method classifies the user's query to determine intent,
        then routes to the appropriate specialized agent.
        
        Args:
            user_message: The user's message/question
            conversation_history: Previous messages in the conversation
            context: Additional context (task info, etc.)
            force_intent: Override automatic classification with specific intent
            
        Returns:
            ChatResponse with the assistant's reply and routing metadata
        """
        # Convert conversation history to dict format
        history_dicts = []
        if conversation_history:
            for msg in conversation_history:
                history_dicts.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Route through agent workflow
        routed_response: RoutedResponse = await self._agent_router.route(
            query=user_message,
            conversation_history=history_dicts,
            context=context or {},
            force_intent=force_intent
        )
        
        return ChatResponse(
            message=routed_response.message,
            context_used=routed_response.context_used,
            intent=routed_response.intent.value,
            agent_type=routed_response.agent_type,
            classification_confidence=routed_response.confidence
        )

    async def chat_with_routing_stream(
        self,
        user_message: str,
        conversation_history: list[ChatMessage] = None,
        context: dict = None,
        force_intent: QueryIntent = None,
    ) -> AsyncIterator[str]:
        """
        Chat with routing, streaming response content chunk by chunk.
        """
        history_dicts = []
        if conversation_history:
            for msg in conversation_history:
                history_dicts.append({"role": msg.role, "content": msg.content})
        async for chunk in self._agent_router.route_stream(
            query=user_message,
            conversation_history=history_dicts,
            context=context or {},
            force_intent=force_intent,
        ):
            yield chunk

    async def chat_with_kb(
        self,
        user_message: str,
        conversation_history: list[ChatMessage] = None
    ) -> ChatResponse:
        """
        Chat using the knowledge base for context.
        """
        return ChatResponse(
            message=user_message
        )   
# Global chat service instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create the global chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
