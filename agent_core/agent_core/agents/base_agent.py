"""Base agent interface and shared utilities.

This module provides the base class for specialized agents
in agentic AI applications, along with base input/output Pydantic models.
"""

import importlib.resources
import logging
import re
from typing import AsyncIterator, Optional, Tuple
from pydantic import BaseModel, Field

from agent_core.agents._llm_default import DefaultHFAdapter, LLMCallable
from agent_core.agents.agent_config import AgentConfig, LOCAL_BASE_URL, LOCAL_MODEL
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
     
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_client: Optional[LLMCallable] = None,
    ):
        """
        Initialize the agent with configuration.

        Args:
            config: AgentConfig instance (takes precedence over individual params)
            llm_client: Optional LLM client with chat_async(messages, config) -> LLMResponse.
                If None, uses HuggingFace InferenceClient directly (default).
        """
        if config is not None:
            self._config = config
        else:
            self._config = AgentConfig(
                model=LOCAL_MODEL,
                provider="huggingface",
                api_key="local_api_key",
                base_url=LOCAL_BASE_URL,
                max_tokens=4096,
                temperature=0.7,
                use_rag=False,
                rag_top_k=3,
                rag_category="default",
            )
        self._llm_client = llm_client if llm_client is not None else DefaultHFAdapter()
        
        # Load system prompt from agent_dir (filesystem or resources)
        if self._config.sys_prompt is None:
            self._config.sys_prompt = self._load_system_prompt()
        
        self.agent_type = self._config.name or "BaseAgent"
        self.rag_service = RAGService()
    
    def _load_system_prompt(self) -> str:
        """
        Load system prompt from agent_dir (filesystem or package resources).
        
        Returns:
            System prompt text, or default prompt if not found
        """
        # Check if this is a resource-based agent
        # Resource-based agents have agent_dir set to Path("__resource__")
        is_resource = (
            self._config.agent_dir is not None and
            str(self._config.agent_dir) == "__resource__"
        ) or (
            self._config.agent_dir is None and
            '_resource_package' in self._config.extra
        )
        
        if is_resource:
            # Load from package resources
            return self._load_prompt_from_resources()
        else:
            # Load from filesystem
            return self._load_prompt_from_filesystem()
    
    def _load_prompt_from_resources(self) -> str:
        """Load prompt from package resources."""
        try:
            # Get resource path from config extra
            package = self._config.extra.get('_resource_package', 'agent_core.agents.config')
            resource_path = self._config.extra.get('_resource_path', self._config.name)
            prompt_path = f"{resource_path}/prompt.md"
            
            config_files = importlib.resources.files(package)
            prompt_file = config_files / prompt_path
            
            prompt_text = prompt_file.read_text(encoding="utf-8")
            logger.debug(f"Loaded prompt from resources for agent: {self._config.name}")
            return prompt_text
        except (FileNotFoundError, ModuleNotFoundError, AttributeError, KeyError) as e:
            logger.debug(f"Prompt not found in resources for {self._config.name}: {e}")
            return "You are a helpful assistant."
    
    def _load_prompt_from_filesystem(self) -> str:
        """Load prompt from filesystem."""
        if self._config.agent_dir is None:
            return "You are a helpful assistant."
        
        prompt_path = self._config.agent_dir / "prompt.md"
        if prompt_path.exists():
            try:
                prompt_text = prompt_path.read_text()
                logger.debug(f"Loaded prompt from filesystem for agent: {self._config.name}")
                return prompt_text
            except Exception as e:
                logger.error(f"Failed to load prompt for {self._config.name}: {e}")
                return "You are a helpful assistant."
        else:
            return "You are a helpful assistant."

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
        print("\n----\nSend request to LLM....\n")
        response = await self._llm_client.chat_async(messages=messages, config=self._config)
        response_content = response.content
        return AgentResponse(
            message=response_content,
            context_used=context_used,
            agent_type=self.agent_type,
            metadata={"rag_enabled": should_use_rag and self.rag_service is not None}
        )

    async def execute_stream(self, input_data: AgentInput) -> AsyncIterator[str]:
        """
        Execute the agent and stream response content chunk by chunk.

        Uses chat_async_stream on the LLM client when available; otherwise
        falls back to chat_async and yields the full message as one chunk.
        """
        messages, _context_used, _should_use_rag = await self._build_messages(input_data)
        stream_method = getattr(self._llm_client, "chat_async_stream", None)
        if callable(stream_method):
            async for chunk in stream_method(messages, self._config):
                yield chunk
        else:
            response = await self._llm_client.chat_async(messages=messages, config=self._config)
            if response.content:
                yield response.content

    async def _build_messages(self, input_data: AgentInput) -> Tuple[list[dict], list[dict], bool]:
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

        
        context = context or {}
        
        # Get filter parameters from context or defaults
        category = context.get("rag_category", getattr(self._config, "rag_category", None))
        knowledge_ids = context.get("knowledge_ids")
        top_k = context.get("rag_top_k", getattr(self._config, "rag_top_k", 3))
        
        try:
            results = await self.rag_service.search(
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
            context: Optional context dict for template substitution.
                     Keys in this dict will be used to replace placeholders
                     in the format {key} in the prompt string. Only placeholders
                     that exist in context will be substituted; others remain as-is.
            
        Returns:
            The system prompt string
        """
        if self._config.sys_prompt:
            # Use injected prompt, with optional context substitution
            prompt = self._config.sys_prompt
            if context:
                # Substitute placeholders in format {key} with values from context
                # Only substitute keys that exist in context, leave others as-is
                def replace_placeholder(match):
                    key = match.group(1)
                    if key in context:
                        value = context[key]
                        # Handle None values by converting to empty string
                        return str(value) if value is not None else ""
                    # Return original placeholder if key not in context
                    return match.group(0)
                
                # Match placeholders in format {key} where key is a valid identifier
                prompt = re.sub(r'\{(\w+)\}', replace_placeholder, prompt)
            return prompt
        return "You are a helpful assistant."


