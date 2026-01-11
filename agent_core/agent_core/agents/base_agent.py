"""Base agent interface and shared utilities.

This module provides the base class for specialized agents
in agentic AI applications, along with base input/output Pydantic models.
"""

import logging
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from agent_core.client import LLMClient
from agent_core.types import Message as LLMMessage, LLMResponse

if TYPE_CHECKING:
    from agent_core.agents.factory import AgentConfig
    from agent_core.services.rag.service import RAGService

logger = logging.getLogger(__name__)


class AgentInput(BaseModel):
    """
    Base input for all agents.
    
    This model provides the standard input structure for agent execution.
    Agents may extend this with additional fields in their configuration.
    
    Attributes:
        query: The user's input query
        conversation_history: Previous messages in the conversation
        context: Additional context (entities, metadata, task info, etc.)
    """
    query: str
    conversation_history: list[dict] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent execution (extended output with full context)."""
    message: str
    context_used: list[dict] = Field(default_factory=list)
    model: str = ""
    provider: str = ""
    agent_type: str = ""
    metadata: dict = Field(default_factory=dict)


class BaseAgent:
    """
    Base class for specialized agents.
    
    Each agent handles a specific type of query intent.
    Uses LLMClient for LLM integration.
    
    Can be used directly for simple pass-through queries, or subclassed
    for specialized behavior.
    
    Example:
        # Direct usage
        agent = BaseAgent(provider="huggingface", model="llama3")
        response = await agent.execute("What is Python?")
        
        # Subclass for custom behavior
        class MyAgent(BaseAgent):
            agent_type = "my_agent"
            
            def build_system_prompt(self, context=None):
                return "You are an expert in Python programming."
    """
    
    agent_type: str = "base"
    
    def __init__(
        self,
        # AgentConfig for unified configuration
        config: "AgentConfig" = None,
        # Convenience parameters for creating config
        provider: str = None,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        # System prompt injection from factory
        system_prompt: str = None,
        # RAG configuration
        rag_service: "RAGService" = None,
        use_rag: bool = False,
        rag_top_k: int = 5,
        rag_category: str = None
    ):
        """
        Initialize the agent with configuration.
        
        Args:
            config: AgentConfig instance (takes precedence over individual params)
            provider: LLM provider name (huggingface)
            model: Model name
            api_key: API key for the provider
            base_url: Custom base URL for the API
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system_prompt: System prompt loaded from config (overrides build_system_prompt)
            rag_service: RAGService instance for retrieval-augmented generation
            use_rag: Whether to use RAG for context retrieval (default False)
            rag_top_k: Number of results to retrieve from RAG (default 5)
            rag_category: Optional category filter for RAG searches
        """
        from agent_core.agents.factory import AgentConfig
        
        if config is not None:
            # Use AgentConfig directly
            self._config = config
            self._system_prompt = system_prompt
        else:
            # Build config from individual parameters
            self._config = AgentConfig(
                provider=provider or "huggingface",
                model=model or "mistral:7b-instruct",
                api_key=api_key,
                base_url=base_url,
                max_tokens=max_tokens,
                temperature=temperature
            )
            self._system_prompt = system_prompt
        
        self._llm_client = LLMClient(self._config)
        
        # Expose config values for convenience
        self.provider = self._config.provider
        self.model = self._config.model
        
        # RAG configuration
        self._rag_service = rag_service
        self._use_rag = use_rag
        self._rag_top_k = rag_top_k
        self._rag_category = rag_category

    async def execute(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None,
        use_rag: Optional[bool] = None
    ) -> AgentResponse:
        """
        Execute the agent with the given query.
        
        Default implementation passes the query directly to the LLM
        with the system prompt and conversation history. If RAG is enabled,
        retrieves relevant context from the knowledge base first.
        
        Args:
            query: User's input query
            conversation_history: Previous messages in conversation
            context: Additional context (entities, metadata, etc.)
            use_rag: Override RAG setting for this call (None uses default)
            
        Returns:
            AgentResponse with the result
        """
        context = context or {}
        context_used = []
        
        # Determine if RAG should be used
        should_use_rag = use_rag if use_rag is not None else self._use_rag
        
        # Retrieve RAG context if enabled
        rag_context = ""
        if should_use_rag and self._rag_service:
            rag_results = await self._retrieve_rag_context(query, context)
            if rag_results:
                context_used = rag_results
                rag_context = self._format_rag_context(rag_results)
        
        messages = []
        
        # Add system prompt
        system_prompt = self.build_system_prompt(context)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add RAG context as a system message if available
        if rag_context:
            messages.append({
                "role": "system", 
                "content": f"Use the following context to help answer the user's question:\n\n{rag_context}"
            })
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add user query
        messages.append({"role": "user", "content": query})
        
        # Call LLM
        response = await self._call_llm(messages)
        
        return AgentResponse(
            message=response,
            context_used=context_used,
            model=self.model,
            provider=self.provider,
            agent_type=self.agent_type,
            metadata={"rag_enabled": should_use_rag and self._rag_service is not None}
        )
    
    async def _retrieve_rag_context(
        self,
        query: str,
        context: Optional[dict] = None
    ) -> list[dict]:
        """
        Retrieve relevant context from the RAG service.
        
        Args:
            query: The user's query to search for
            context: Optional context with filters (category, knowledge_ids)
            
        Returns:
            List of context dicts with content, title, uri, and score
        """
        if not self._rag_service:
            return []
        
        context = context or {}
        
        # Get filter parameters from context or defaults
        category = context.get("rag_category", self._rag_category)
        knowledge_ids = context.get("knowledge_ids")
        top_k = context.get("rag_top_k", self._rag_top_k)
        
        try:
            results = await self._rag_service.search(
                query=query,
                n_results=top_k,
                category=category,
                knowledge_ids=knowledge_ids
            )
            
            return [
                {
                    "content": r.content,
                    "title": r.title,
                    "uri": r.uri,
                    "score": r.score,
                    "knowledge_id": r.knowledge_id
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return []
    
    def _format_rag_context(self, results: list[dict]) -> str:
        """
        Format RAG results into a context string for the LLM.
        
        Args:
            results: List of RAG result dicts
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "Unknown")
            content = result.get("content", "")
            context_parts.append(f"[{i}] {title}:\n{content}")
        
        return "\n\n---\n\n".join(context_parts)

    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """
        Build the system prompt for this agent.
        
        If a system_prompt was injected via constructor (from config),
        it will be used. Otherwise, subclasses should override this method.
        
        Args:
            context: Optional context dict for template substitution
            
        Returns:
            The system prompt string
        """
        if self._system_prompt:
            # Use injected prompt, with optional context substitution
            prompt = self._system_prompt
            if context:
                try:
                    prompt = prompt.format(**context)
                except KeyError:
                    # If format fails, return as-is
                    pass
            return prompt
        return "You are a helpful assistant."

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
