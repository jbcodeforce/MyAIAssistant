"""Query classification agent for intent detection and routing.

This module provides intent classification for user queries to enable
intelligent routing to specialized agents.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from agent_core.agents.base_agent import BaseAgent, AgentResponse

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Enumeration of possible query intents."""
    
    # Knowledge/RAG related queries
    KNOWLEDGE_SEARCH = "knowledge_search"
    
    # Task/todo related queries  
    TASK_PLANNING = "task_planning"
    TASK_STATUS = "task_status"
    
    # General conversation
    GENERAL_CHAT = "general_chat"
    
    # Code/technical assistance
    CODE_HELP = "code_help"
    RESEARCH = "research"
    # Clarification needed
    UNCLEAR = "unclear"


@dataclass
class ClassificationResult[AgentResponse]:
    """Result of query classification."""
    intent: QueryIntent
    confidence: float
    reasoning: str
    entities: dict  # Extracted entities from the query
    suggested_context: Optional[str] = None


# Default classification prompt (used if no prompt.md is provided)
CLASSIFICATION_PROMPT = """You are a query classification agent. Analyze the user's query and determine its intent.

Classify the query into one of these categories:
- knowledge_search: User wants to find information from their knowledge base/documents
- task_planning: User wants help planning, organizing, or breaking down a task
- task_status: User is asking about the status of existing tasks or todos
- general_chat: General conversation or questions not related to documents or tasks
- code_help: User needs help with code, programming, or technical implementation
- unclear: The query is ambiguous and needs clarification

Respond with a JSON object containing:
{{
    "intent": "<one of the categories above>",
    "confidence": <0.0 to 1.0>,
    "reasoning": "<brief explanation of why this classification>",
    "entities": {{
        "topic": "<main topic if identified>",
        "action": "<requested action if any>",
        "keywords": ["<relevant keywords>"]
    }},
    "suggested_context": "<optional: what additional context might help>"
}}

User Query: {query}

Respond ONLY with the JSON object, no additional text."""


class QueryClassifier(BaseAgent):
    """
    Agent that classifies user queries to determine routing.
    
    Extends BaseAgent to support factory-based creation and config injection.
    Uses LLMClient to analyze query intent and extract relevant entities.
    
    Example:
        # Direct instantiation
        config = LLMConfig(provider="openai", model="gpt-4", api_key="...")
        classifier = QueryClassifier(llm_config=config)
        
        result = await classifier.classify("How do I implement OAuth?")
        print(result.intent)  # QueryIntent.CODE_HELP
        
        # Or via factory
        factory = AgentFactory()
        classifier = factory.create_agent("QueryClassifier")
    """
    
    agent_type = "query_classifier"
    
    def __init__(
        self,
        # Convenience parameters for creating config
        provider: str = None,
        model: str = None,
        api_key: str = None,
        base_url: str = None,
        max_tokens: int = 500,
        temperature: float = 0.1,
        # System prompt from factory
        system_prompt: str = None
    ):
        """
        Initialize the classifier with LLM configuration.
        
        Args:
            provider: LLM provider name
            model: Model name
            api_key: API key for the provider
            base_url: Custom base URL for the API
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (low for consistent classification)
            system_prompt: System prompt loaded from config
        """
        # Call BaseAgent constructor
        super().__init__(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt
        )

    async def execute(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None
    ) -> AgentResponse:
        """
        Execute the classifier agent (BaseAgent interface).
        
        This wraps the classify method for compatibility with the
        standard agent interface.
        
        Args:
            query: User's input query
            conversation_history: Previous messages in conversation
            context: Additional context
            
        Returns:
            AgentResponse with classification result in metadata
        """
        result = await self.classify(query, conversation_history)
        
        return AgentResponse(
            message=result.reasoning,
            context_used=[],
            model=self.model,
            provider=self.provider,
            agent_type=self.agent_type,
            metadata={
                "intent": result.intent.value,
                "confidence": result.confidence,
                "entities": result.entities,
                "suggested_context": result.suggested_context
            }
        )

    async def classify(
        self,
        query: str,
        conversation_context: Optional[list[dict]] = None
    ) -> ClassificationResult:
        """
        Classify a user query to determine its intent.
        
        Args:
            query: The user's input query
            conversation_context: Optional previous conversation for context
            
        Returns:
            ClassificationResult with intent and metadata
        """
        prompt = self.build_system_prompt({"query": query})
        
        # Add conversation context if available
        if conversation_context:
            context_summary = self._summarize_context(conversation_context)
            prompt = f"Previous conversation context:\n{context_summary}\n\n{prompt}"
        
        try:
            response_text = await self._call_llm_for_classification(prompt)
            return self._parse_response(response_text)
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return ClassificationResult(
                intent=QueryIntent.GENERAL_CHAT,
                confidence=0.5,
                reasoning=f"Classification failed, defaulting to general chat: {str(e)}",
                entities={}
            )

    def classify_sync(
        self,
        query: str,
        conversation_context: Optional[list[dict]] = None
    ) -> ClassificationResult:
        """
        Classify a user query synchronously.
        
        Args:
            query: The user's input query
            conversation_context: Optional previous conversation for context
            
        Returns:
            ClassificationResult with intent and metadata
        """
        prompt = self.build_system_prompt({"query": query})
        
        if conversation_context:
            context_summary = self._summarize_context(conversation_context)
            prompt = f"Previous conversation context:\n{context_summary}\n\n{prompt}"
        
        try:
            response_text = self._call_llm_sync_for_classification(prompt)
            return self._parse_response(response_text)
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return ClassificationResult(
                intent=QueryIntent.GENERAL_CHAT,
                confidence=0.5,
                reasoning=f"Classification failed, defaulting to general chat: {str(e)}",
                entities={}
            )

    def build_system_prompt(self, context: Optional[dict] = None) -> str:
        """
        Build the classification prompt.
        
        Uses injected system_prompt if available, otherwise falls back
        to the default CLASSIFICATION_PROMPT.
        
        Args:
            context: Dict containing 'query' for template substitution
            
        Returns:
            The prompt string with query substituted
        """
        context = context or {}
        query = context.get("query", "")
        
        if self._system_prompt:
            # Use injected prompt from config
            try:
                return self._system_prompt.format(query=query)
            except KeyError:
                return self._system_prompt
        
        # Fall back to default prompt
        return CLASSIFICATION_PROMPT.format(query=query)

    def _summarize_context(self, context: list[dict]) -> str:
        """Summarize conversation context for classification."""
        summary_parts = []
        for msg in context[-3:]:  # Last 3 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]
            summary_parts.append(f"{role}: {content}")
        return "\n".join(summary_parts)

    def _parse_response(self, response_text: str) -> ClassificationResult:
        """Parse LLM response into ClassificationResult."""
        try:
            # Try to extract JSON from the response
            json_str = response_text.strip()
            if json_str.startswith("```"):
                # Handle markdown code blocks
                lines = json_str.split("\n")
                json_str = "\n".join(lines[1:-1])
            
            data = json.loads(json_str)
            
            intent_str = data.get("intent", "general_chat")
            try:
                intent = QueryIntent(intent_str)
            except ValueError:
                intent = QueryIntent.GENERAL_CHAT
            
            return ClassificationResult(
                intent=intent,
                confidence=float(data.get("confidence", 0.7)),
                reasoning=data.get("reasoning", ""),
                entities=data.get("entities", {}),
                suggested_context=data.get("suggested_context")
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse classification response: {e}")
            return ClassificationResult(
                intent=QueryIntent.GENERAL_CHAT,
                confidence=0.5,
                reasoning="Failed to parse classification response",
                entities={}
            )

    async def _call_llm_for_classification(self, prompt: str) -> str:
        """Call the LLM asynchronously for classification."""
        messages = [{"role": "user", "content": prompt}]
        return await self._call_llm(messages)

    def _call_llm_sync_for_classification(self, prompt: str) -> str:
        """Call the LLM synchronously for classification."""
        messages = [{"role": "user", "content": prompt}]
        return self._call_llm_sync(messages)


# Singleton instance
_classifier: Optional[QueryClassifier] = None


def get_query_classifier() -> QueryClassifier:
    """Get or create the global query classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifier()
    return _classifier


def reset_query_classifier() -> None:
    """Reset the global classifier instance. Useful for testing."""
    global _classifier
    _classifier = None
