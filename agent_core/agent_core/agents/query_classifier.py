"""Query classification agent for intent detection and routing.

This module provides intent classification for user queries to enable
intelligent routing to specialized agents.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from agent_core.client import LLMClient
from agent_core.config import LLMConfig
from agent_core.types import Message as LLMMessage

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
class ClassificationResult:
    """Result of query classification."""
    intent: QueryIntent
    confidence: float
    reasoning: str
    entities: dict  # Extracted entities from the query
    suggested_context: Optional[str] = None


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


class QueryClassifier:
    """
    Agent that classifies user queries to determine routing.
    
    Uses LLMClient to analyze query intent and extract relevant entities.
    
    Example:
        config = LLMConfig(provider="openai", model="gpt-4", api_key="...")
        classifier = QueryClassifier(llm_config=config)
        
        result = await classifier.classify("How do I implement OAuth?")
        print(result.intent)  # QueryIntent.CODE_HELP
    """
    
    def __init__(
        self,
        llm_config: LLMConfig = None,
        llm_client: LLMClient = None,
        # Convenience parameters for creating config
        provider: str = None,
        model: str = None,
        api_key: str = None,
        base_url: str = None
    ):
        """
        Initialize the classifier with LLM configuration.
        
        Args:
            llm_config: Pre-built LLM configuration (takes precedence)
            llm_client: Pre-built LLM client (takes precedence over config)
            provider: LLM provider name
            model: Model name
            api_key: API key for the provider
            base_url: Custom base URL for the API
        """
        if llm_client:
            self._llm_client = llm_client
            self._llm_config = llm_client.config
        elif llm_config:
            self._llm_config = llm_config
            self._llm_client = LLMClient(llm_config)
        else:
            # Build config from individual parameters
            # Use low temperature for consistent classification
            # Default to huggingface with local server
            self._llm_config = LLMConfig(
                provider=provider or "huggingface",
                model=model or "llama3",
                api_key=api_key,
                base_url=base_url or "http://localhost:8080",
                max_tokens=500,
                temperature=0.1,
                timeout=30.0,
                response_format=None
            )
            self._llm_client = LLMClient(self._llm_config)
        
        self.provider = self._llm_config.provider
        self.model = self._llm_config.model

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
        prompt = CLASSIFICATION_PROMPT.format(query=query)
        
        # Add conversation context if available
        if conversation_context:
            context_summary = self._summarize_context(conversation_context)
            prompt = f"Previous conversation context:\n{context_summary}\n\n{prompt}"
        
        try:
            response_text = await self._call_llm(prompt)
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
        prompt = CLASSIFICATION_PROMPT.format(query=query)
        
        if conversation_context:
            context_summary = self._summarize_context(conversation_context)
            prompt = f"Previous conversation context:\n{context_summary}\n\n{prompt}"
        
        try:
            response_text = self._call_llm_sync(prompt)
            return self._parse_response(response_text)
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return ClassificationResult(
                intent=QueryIntent.GENERAL_CHAT,
                confidence=0.5,
                reasoning=f"Classification failed, defaulting to general chat: {str(e)}",
                entities={}
            )

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

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM asynchronously."""
        messages = [LLMMessage(role="user", content=prompt)]
        response = await self._llm_client.chat_async(messages)
        return response.content

    def _call_llm_sync(self, prompt: str) -> str:
        """Call the LLM synchronously."""
        messages = [LLMMessage(role="user", content=prompt)]
        response = self._llm_client.chat(messages)
        return response.content


# Singleton instance
_classifier: Optional[QueryClassifier] = None


def get_query_classifier() -> QueryClassifier:
    """Get or create the global query classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifier()
    return _classifier
