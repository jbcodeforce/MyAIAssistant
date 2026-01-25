"""Base agent interface and shared utilities.

This module provides the base class for specialized agents
in agentic AI applications, along with base input/output Pydantic models.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field

from agent_core.types import Message as LLMMessage, LLMResponse
from agent_core.providers.llm_provider_factory import LLMProviderFactory

from agent_core.agents.agent_factory import AgentConfig
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
        use_rag: Override RAG setting for this call (None uses instance default)
    """
    query: str
    conversation_history: list[dict] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
    use_rag: Optional[bool] = False


class AgentResponse(BaseModel):
    """Response from an agent execution (extended output with full context)."""
    message: str
    context_used: list[dict] = Field(default_factory=list)
    agent_type: str = ""
    metadata: dict = Field(default_factory=dict)


class BaseAgent:
    """
    Base class for specialized agents.
    
    Each agent handles a specific type of query intent.
    
    Can be used directly for simple pass-through queries, or subclassed
    for specialized behavior.
    
    Example:
        # Direct usage
        agent = BaseAgent(config=AgentConfig(model="llama3"))
        response = await agent.execute(AgentInput(query="What is Python?"))
    """
    
    agent_type: str = "general"
    
    def __init__(
        self,
        # AgentConfig for unified configuration
        config: AgentConfig = None
    ):
        """
        Initialize the agent with configuration.
        
        Args:
            config: AgentConfig instance (takes precedence over individual params)
        """

        if config is not None:
            # Use AgentConfig directly
            self._config = config
        else:
            # Build config from individual parameters
            self._config = AgentConfig(
                model="mistral:7b-instruct",
                provider="huggingface",
                api_key="local_api_key",
                base_url="http://localhost:11434/v1",
                max_tokens=2048,
                temperature=0.7,
                use_rag=False,
                rag_top_k=5,
                rag_category=None
            )
        self._llm_client = LLMProviderFactory.create_provider(self._config.provider)
        prompt_path = self._config.agent_dir / "prompt.md"
        if prompt_path.exists():
            try:
                self._system_prompt = prompt_path.read_text()
                logger.debug(f"Loaded prompt for agent: {self._config.name}")
            except Exception as e:
                logger.error(f"Failed to load prompt for {self._config.name}: {e}")
        else:
            self._system_prompt = "You are a helpful assistant."

    async def execute(
        self,
        input_data: AgentInput
    ) -> AgentResponse:
        """
        Execute the agent with the given input.
        
        Default implementation passes the query directly to the LLM
        with the system prompt and conversation history. If RAG is enabled,
        retrieves relevant context from the knowledge base first.
        
        Args:
            input_data: AgentInput containing query, conversation history, context, and use_rag override
            
        Returns:
            AgentResponse with the result
        """
        messages, context_used, should_use_rag= await self._build_messages(input_data)
        # Call LLM
        response = await self._call_llm(messages)
        
        return AgentResponse(
            message=response,
            context_used=context_used,
            agent_type=self.agent_type,
            metadata={"rag_enabled": should_use_rag and self._rag_service is not None}
        )
    
    async def _build_messages(self, input_data: AgentInput) -> list[dict]:
        """
        Process the input data for the agent.
        
        Args:
            input_data: AgentInput containing query, conversation history, context, and use_rag override
            
        Returns:
            List of context dicts with content, title, uri, and score
        """
        context = input_data.context or {}
        context_used = []
        
        # Determine if RAG should be used
        should_use_rag = input_data.use_rag if input_data.use_rag is not None else self._config.use_rag
        
        # Retrieve RAG context if enabled
        rag_context = ""
        if should_use_rag:
            rag_results = await self._retrieve_rag_context(input_data.query, context)
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
        if input_data.conversation_history:
            messages.extend(input_data.conversation_history)
        
        # Add user query
        messages.append({"role": "user", "content": input_data.query})
        
        return messages, context_used, should_use_rag

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
        _rag_service = RAGService()
        
        context = context or {}
        
        # Get filter parameters from context or defaults
        category = context.get("rag_category", self._rag_category)
        knowledge_ids = context.get("knowledge_ids")
        top_k = context.get("rag_top_k", self._rag_top_k)
        
        try:
            results = await _rag_service.search(
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

    def  build_system_prompt(self, context: Optional[dict] = None) -> str:
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
        
        response: LLMResponse = await self._llm_client.chat_async(messages=llm_messages, config=self._config)
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
        
        response: LLMResponse = self._llm_client.chat_sync(messages=llm_messages, config=self._config)
        return response.content
