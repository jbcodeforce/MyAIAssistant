"""Chat service for LLM-powered task planning with RAG integration."""

import logging
from dataclasses import dataclass
from typing import Optional

from agent_core import LLMClient, AgentConfig, Message as LLMMessage

from app.core.config import get_settings
from agent_core.services.rag.service import RAGService, get_rag_service
from agent_core.agents.query_classifier import QueryIntent
from agent_core.agents.agent_router import  RoutedResponse, get_agent_router, reset_agent_router

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
        self,
        provider: str = None,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        max_tokens: int = None,
        temperature: float = None,
        rag_service: RAGService = None
    ):
        settings = get_settings()
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.llm_api_key
        self.base_url = base_url or settings.llm_base_url
        self.max_tokens = max_tokens or settings.llm_max_tokens
        self.temperature = temperature or settings.llm_temperature
        self.rag_service = rag_service or get_rag_service()
        
        # Create LLM client configuration
        self._llm_config = AgentConfig(
            provider=self.provider,
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        logger.info(f"LLM config: {self._llm_config}")
        # Create LLM client
        self._llm_client = LLMClient(self._llm_config)
        
        # Initialize agent router with this config
        # Reset first to ensure it uses our config
        reset_agent_router()
        self._agent_router = get_agent_router(self._llm_config)

    async def chat_with_todo(
        self,
        todo_title: str,
        todo_description: Optional[str],
        user_message: str,
        conversation_history: list[ChatMessage] = None,
        use_rag: bool = True,
        rag_query: Optional[str] = None
    ) -> ChatResponse:
        """
        Chat about a todo task, optionally using RAG for context.
        
        Args:
            todo_title: Title of the todo task
            todo_description: Optional description of the task
            user_message: The user's message/question
            conversation_history: Previous messages in the conversation
            use_rag: Whether to use RAG to retrieve relevant context
            rag_query: Custom query for RAG (defaults to combining todo + message)
            
        Returns:
            ChatResponse with the assistant's reply and context used
        """
        context_used = []
        context_text = ""
        
        # Retrieve relevant context from knowledge base
        if use_rag:
            query = rag_query or f"{todo_title} {user_message}"
            rag_results = await self.rag_service.search(query, n_results=3)
            
            if rag_results:
                context_parts = []
                for result in rag_results:
                    context_parts.append(f"[From: {result.title}]\n{result.content}")
                    context_used.append({
                        "title": result.title,
                        "uri": result.uri,
                        "score": result.score,
                        "snippet": result.content[:200] + "..." if len(result.content) > 200 else result.content
                    })
                context_text = "\n\n---\n\n".join(context_parts)

        # Build the system prompt
        system_prompt = self._build_system_prompt(
            todo_title=todo_title,
            todo_description=todo_description,
            context=context_text
        )
        
        # Build messages
        messages = [LLMMessage(role="system", content=system_prompt)]
        
        if conversation_history:
            for msg in conversation_history:
                messages.append(LLMMessage(role=msg.role, content=msg.content))
        
        messages.append(LLMMessage(role="user", content=user_message))
        
        # Call the LLM
        response = await self._llm_client.chat_async(messages)
        
        return ChatResponse(
            message=response.content,
            context_used=context_used
        )

    async def chat_with_rag(
        self,
        user_message: str,
        conversation_history: list[ChatMessage] = None,
        n_results: int = 5
    ) -> ChatResponse:
        """
        Chat using the RAG knowledge base for context.
        
        This is a general-purpose chat that uses the knowledge base
        to answer questions, without being tied to a specific task.
        
        Args:
            user_message: The user's message/question
            conversation_history: Previous messages in the conversation
            n_results: Number of RAG results to retrieve
            
        Returns:
            ChatResponse with the assistant's reply and context used
        """
        context_used = []
        context_text = ""
        
        # Retrieve relevant context from knowledge base
        rag_results = await self.rag_service.search(user_message, n_results=n_results)
        
        if rag_results:
            context_parts = []
            for result in rag_results:
                context_parts.append(f"[From: {result.title}]\n{result.content}")
                context_used.append({
                    "title": result.title,
                    "uri": result.uri,
                    "score": result.score,
                    "snippet": result.content[:200] + "..." if len(result.content) > 200 else result.content
                })
            context_text = "\n\n---\n\n".join(context_parts)

        # Build the system prompt
        system_prompt = self._build_rag_system_prompt(context=context_text)
        
        # Build messages
        messages = [LLMMessage(role="system", content=system_prompt)]
        
        if conversation_history:
            for msg in conversation_history:
                messages.append(LLMMessage(role=msg.role, content=msg.content))
        
        messages.append(LLMMessage(role="user", content=user_message))
        
        # Call the LLM
        response = await self._llm_client.chat_async(messages)
        
        return ChatResponse(
            message=response.content,
            context_used=context_used,
            model=self.model,
            provider=self.provider
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

    def _build_system_prompt(
        self,
        todo_title: str,
        todo_description: Optional[str],
        context: str
    ) -> str:
        """Build the system prompt for the LLM."""
        prompt_parts = [
            "You are a helpful AI assistant that helps users plan and execute tasks.",
            "You provide clear, actionable advice and break down complex tasks into manageable steps.",
            "",
            f"## Current Task",
            f"**Title:** {todo_title}"
        ]
        
        if todo_description:
            prompt_parts.append(f"**Description:** {todo_description}")
        
        if context:
            prompt_parts.extend([
                "",
                "## Relevant Knowledge Base Context",
                "Use this context to provide informed advice:",
                "",
                context
            ])
        
        prompt_parts.extend([
            "",
            "## Instructions",
            "- Help the user understand how to approach and complete this task",
            "- Break down complex tasks into clear, actionable steps",
            "- Reference the knowledge base context when relevant",
            "- Be concise but thorough",
            "- Ask clarifying questions if needed"
        ])
        
        return "\n".join(prompt_parts)

    def _build_rag_system_prompt(self, context: str) -> str:
        """Build the system prompt for RAG-based chat."""
        prompt_parts = [
            "You are a helpful AI assistant with access to a knowledge base.",
            "Answer the user's questions using the provided context from the knowledge base.",
            "If the context doesn't contain relevant information, say so clearly.",
        ]
        
        if context:
            prompt_parts.extend([
                "",
                "## Knowledge Base Context",
                "Use this context to answer the user's question:",
                "",
                context
            ])
        else:
            prompt_parts.extend([
                "",
                "## Note",
                "No relevant context was found in the knowledge base for this query.",
                "Answer based on your general knowledge, but inform the user that",
                "the answer is not based on their indexed documents."
            ])
        
        prompt_parts.extend([
            "",
            "## Instructions",
            "- Answer questions based on the provided context",
            "- Cite the source document when referencing specific information",
            "- Be concise and accurate",
            "- If the context is insufficient, acknowledge the limitation"
        ])
        
        return "\n".join(prompt_parts)


# Global chat service instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create the global chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
