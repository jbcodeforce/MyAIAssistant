"""Agent router for query classification and routing workflow.

This module implements the main routing workflow that:
1. Classifies incoming queries
2. Routes to appropriate specialized agents
3. Orchestrates the response generation
"""

import logging
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field
from agent_core.agents.agent_factory import AgentConfig, get_agent_factory

from agent_core.agents.base_agent import BaseAgent, AgentResponse, AgentInput
from agent_core.agents.query_classifier import (
    QueryClassifier,
    ClassificationResult,
    QueryIntent,
)

logger = logging.getLogger(__name__)


class WorkflowState(BaseModel):
    """State passed through the routing workflow."""
    model_config = {"arbitrary_types_allowed": True}
    query: str
    conversation_history: list[dict] = Field(default_factory=list)
    classification: Optional[ClassificationResult] = None
    agent_response: Optional[AgentResponse] = None
    context: dict = Field(default_factory=dict)
    error: Optional[str] = None


class RoutedResponse(BaseModel):
    """Final response from the routing workflow."""
    message: str
    context_used: list[dict]
    intent: QueryIntent
    confidence: float
    agent_type: str
    classification_reasoning: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRouter:
    """
    Router that classifies queries and routes to specialized agents.
    
    Implements a classification-then-routing pattern:
    1. Query Classification: Determine user intent
    2. Agent Selection: Choose appropriate agent based on intent
    3. Execution: Run selected agent
    4. Response: Return formatted response with metadata
    
    Example:
        # Create router
        router = AgentRouter()
        query = "How do I implement OAuth?"
        response = await router.route(query)
    """
    
    # Default intent to agent type mapping
    DEFAULT_INTENT_MAPPING = {
        QueryIntent.KNOWLEDGE_SEARCH: "knowledge_search",
        QueryIntent.TASK_PLANNING: "task_planning",
        QueryIntent.TASK_STATUS: "task_status",
        QueryIntent.CODE_HELP: "code_help",
        QueryIntent.GENERAL_CHAT: "general_chat",
        QueryIntent.UNCLEAR: "unclear",
    }
    
    def __init__(
        self,
        config_dir: Optional[str] = None
    ):
        """
        Initialize the router.
        
        Args:
            config_dir: Optional path to agent configuration directory.
                       If None, uses AgentFactory default.
        """
        factory = get_agent_factory(config_dir=config_dir)

        self.classifier = factory.create_agent("QueryClassifier")
        self.agents: Dict[str, BaseAgent] = {}
        self.intent_mapping = self.DEFAULT_INTENT_MAPPING.copy()
        self.default_agent = factory.create_agent("GeneralAgent")
        self.agents[QueryIntent.KNOWLEDGE_SEARCH] = self.default_agent
        self.agents[QueryIntent.TASK_PLANNING] = factory.create_agent("TaskAgent")
        self.agents[QueryIntent.TASK_STATUS] = self.agents[QueryIntent.TASK_PLANNING]
        self.agents[QueryIntent.CODE_HELP] = factory.create_agent("CodeAgent")
        self.agents[QueryIntent.GENERAL_CHAT] = self.default_agent
        self.agents[QueryIntent.UNCLEAR] = self.default_agent



    async def route(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None,
        force_intent: Optional[QueryIntent] = None
    ) -> RoutedResponse:
        """
        Route a query through classification and agent execution.
        
        Args:
            query: User's input query
            conversation_history: Previous conversation messages
            context: Additional context (task info, etc.)
            force_intent: Override classification with specific intent
            
        Returns:
            RoutedResponse with message and metadata
        """
        state = WorkflowState(
            query=query,
            conversation_history=conversation_history or [],
            context=context or {}
        )
        
        # Step 1: Classify the query
        state = await self._classify_step(state, force_intent)
        
        if state.error:
            return self._error_response(state)
        
        # Step 2: Route to appropriate agent
        state = await self._route_step(state)
        
        if state.error:
            return self._error_response(state)
        
        # Step 3: Build and return response
        return self._build_response(state)


    async def _classify_step(
        self,
        state: WorkflowState,
        force_intent: Optional[QueryIntent] = None
    ) -> WorkflowState:
        """Classification step of the workflow."""
        if force_intent:
            state.classification = ClassificationResult(
                intent=force_intent,
                confidence=1.0,
                reasoning="Intent forced by caller",
                entities={}
            )
            logger.debug(f"Using forced intent: {force_intent}")
            return state
        
        try:
            state.classification = await self.classifier.execute(AgentInput(query=state.query, conversation_history=state.conversation_history))
    
            logger.info(
                f"Classified query as {state.classification.intent} "
                f"(confidence: {state.classification.confidence:.2f})"
            )
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            state.classification = ClassificationResult(
                intent=QueryIntent.GENERAL_CHAT,
                confidence=0.5,
                reasoning=f"Classification failed: {str(e)}",
                entities={}
            )
        
        return state

    async def _route_step(self, state: WorkflowState) -> WorkflowState:
        """Routing step - select and execute appropriate agent."""
        intent = state.classification.intent
        agent_key = self.intent_mapping.get(intent.value, self.default_agent)
        agent = self.agents.get(agent_key)
        
        if not agent:
            state.error = f"No agent available for intent: {intent.value} (agent type: {agent_key})"
            return state
        
        logger.info(f"Routing to {agent_key} agent")
        
        # Prepare context with classification entities
        agent_context = {
            **state.context,
            "entities": state.classification.entities,
            "intent": intent.value,
        }
        
        try:
            input_data = AgentInput(
                query=state.query,
                conversation_history=state.conversation_history,
                context=agent_context
            )
            state.agent_response = await agent.execute(input_data)
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            state.error = f"Agent execution failed: {str(e)}"
        
        return state

    def _build_response(self, state: WorkflowState) -> RoutedResponse:
        """Build final routed response."""
        response = state.agent_response
        classification = state.classification
        
        return RoutedResponse(
            message=response.message,
            context_used=response.context_used,
            intent=classification.intent,
            confidence=classification.confidence,
            agent_type=response.agent_type,
            classification_reasoning=classification.reasoning,
            metadata={
                **response.metadata,
                "entities": classification.entities,
                "suggested_context": classification.suggested_context
            }
        )

    def _error_response(self, state: WorkflowState) -> RoutedResponse:
        """Build error response."""
        return RoutedResponse(
            message=f"I encountered an error processing your request: {state.error}",
            context_used=[],
            intent=QueryIntent.UNCLEAR,
            confidence=0.0,
            agent_type="error",
            classification_reasoning=state.error or "",
            metadata={"error": state.error}
        )

    def get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Get a specific agent by type."""
        return self.agents.get(agent_type)

    def register_agent(self, agent_type: str, agent: BaseAgent) -> None:
        """Register a new agent or replace an existing one."""
        self.agents[agent_type] = agent
        logger.info(f"Registered agent: {agent_type}")

    def add_intent_mapping(self, intent: QueryIntent, agent_type: str) -> None:
        """Add or update intent to agent mapping."""
        self.intent_mapping[intent] = agent_type

