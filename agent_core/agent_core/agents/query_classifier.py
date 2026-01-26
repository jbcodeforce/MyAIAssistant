"""Query classification agent for intent detection and routing.

This module provides intent classification for user queries to enable
intelligent routing to specialized agents.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from agent_core.agents.base_agent import BaseAgent, AgentResponse, AgentInput

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
    
    MEETING_NOTE = "meeting_note"
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


class QueryClassifier(BaseAgent):
    """
    Agent that classifies user queries to determine routing to other agents.
    
    Extends BaseAgent to support factory-based creation and config injection.

    factory = AgentFactory(config_dir=config_dir)
    classifier = factory.create_agent("QueryClassifier")
    """
    
    agent_type = "query_classifier"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    async def execute(
        self,
        input_data: AgentInput
    ) -> ClassificationResult:
        """
        Execute the classifier agent (BaseAgent interface).
        
        This wraps the classify method for compatibility with the
        standard agent interface.
        
        Args:
            input_data: AgentInput containing query and conversation history
            
        Returns:
            AgentResponse with classification result in metadata
        """
        messages, context_used, use_rag = await self._build_messages(input_data)
        
        try:
            response = await self._llm_client.chat_async(messages=messages, config=self._config)
            response_text = response.content
            return self._parse_response(response_text)
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return ClassificationResult(
                intent=QueryIntent.GENERAL_CHAT,
                confidence=0.5,
                reasoning=f"Classification failed, defaulting to general chat: {str(e)}",
                entities={}
            )
        return result


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

