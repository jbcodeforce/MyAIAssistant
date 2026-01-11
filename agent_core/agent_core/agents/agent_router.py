"""Agent router for query classification and routing workflow.

This module implements the main routing workflow that:
1. Classifies incoming queries
2. Routes to appropriate specialized agents
3. Orchestrates the response generation
"""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from agent_core.agents.factory import AgentConfig

from agent_core.agents.base_agent import BaseAgent, AgentResponse
from agent_core.agents.query_classifier import (
    QueryClassifier,
    get_query_classifier,
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
    model: str
    provider: str
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
        # Create agents
        rag_agent = MyRAGAgent(llm_config=config)
        code_agent = MyCodeAgent(llm_config=config)
        general_agent = MyGeneralAgent(llm_config=config)
        
        # Create router
        router = AgentRouter(
            classifier=QueryClassifier(llm_config=config),
            agents={
                "rag": rag_agent,
                "code": code_agent,
                "general": general_agent,
            },
            intent_mapping={
                QueryIntent.KNOWLEDGE_SEARCH: "rag",
                QueryIntent.CODE_HELP: "code",
                QueryIntent.GENERAL_CHAT: "general",
            }
        )
        
        # Route a query
        response = await router.route("How do I implement OAuth?")
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
        classifier: QueryClassifier = None,
        agents: Dict[str, BaseAgent] = None,
        intent_mapping: Dict[QueryIntent, str] = None,
        default_agent: str = "general"
    ):
        """
        Initialize the router.
        
        Args:
            classifier: Query classifier instance
            agents: Dictionary mapping agent type names to agent instances
            intent_mapping: Dictionary mapping intents to agent type names
            default_agent: Default agent type to use when no mapping found
        """
        self.classifier = classifier or get_query_classifier()
        self.agents: Dict[str, BaseAgent] = agents or {}
        self.intent_mapping = intent_mapping or self.DEFAULT_INTENT_MAPPING.copy()
        self.default_agent = default_agent

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

    def route_sync(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None,
        force_intent: Optional[QueryIntent] = None
    ) -> RoutedResponse:
        """
        Route a query synchronously.
        
        Note: This requires agents to implement synchronous execution.
        
        Args:
            query: User's input query
            conversation_history: Previous conversation messages
            context: Additional context
            force_intent: Override classification with specific intent
            
        Returns:
            RoutedResponse with message and metadata
        """
        state = WorkflowState(
            query=query,
            conversation_history=conversation_history or [],
            context=context or {}
        )
        
        # Step 1: Classify
        state = self._classify_step_sync(state, force_intent)
        
        if state.error:
            return self._error_response(state)
        
        # Note: Sync routing requires agents to implement sync execution
        # This is a simplified version - full sync support would need
        # BaseAgent to have execute_sync method
        return self._error_response(WorkflowState(
            query=query,
            error="Synchronous routing requires agent execute_sync implementation"
        ))

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
        
        if not self.classifier:
            state.error = "No classifier configured"
            return state
        
        try:
            state.classification = await self.classifier.classify(
                state.query,
                state.conversation_history
            )
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

    def _classify_step_sync(
        self,
        state: WorkflowState,
        force_intent: Optional[QueryIntent] = None
    ) -> WorkflowState:
        """Synchronous classification step."""
        if force_intent:
            state.classification = ClassificationResult(
                intent=force_intent,
                confidence=1.0,
                reasoning="Intent forced by caller",
                entities={}
            )
            return state
        
        if not self.classifier:
            state.error = "No classifier configured"
            return state
        
        try:
            state.classification = self.classifier.classify_sync(
                state.query,
                state.conversation_history
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
        agent_key = self.intent_mapping.get(intent, self.default_agent)
        agent = self.agents.get(agent_key)
        
        if not agent:
            state.error = f"No agent available for intent: {intent} (agent type: {agent_key})"
            return state
        
        logger.info(f"Routing to {agent_key} agent")
        
        # Prepare context with classification entities
        agent_context = {
            **state.context,
            "entities": state.classification.entities,
            "intent": intent.value,
        }
        
        try:
            state.agent_response = await agent.execute(
                query=state.query,
                conversation_history=state.conversation_history,
                context=agent_context
            )
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
            model=response.model,
            provider=response.provider,
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
            model="",
            provider="",
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

# Singleton instance
_agent_router: Optional[AgentRouter] = None


def get_agent_router(config: "AgentConfig" = None) -> AgentRouter:
    """
    Get or create the global agent router instance.
    
    On first call, creates agents using the provided config.
    Subsequent calls return the cached instance.
    
    Args:
        config: Optional AgentConfig for agents.
                If not provided, agents use default config.
    """
    global _agent_router
    if _agent_router is None:
        _agent_router = _create_default_router(config)
    return _agent_router


def _create_default_router(config: "AgentConfig" = None) -> AgentRouter:
    """Create router with default agent configuration."""
    from agent_core.agents.general_agent import GeneralAgent
    from agent_core.agents.rag_agent import RAGAgent
    from agent_core.agents.code_agent import CodeAgent
    from agent_core.agents.task_agent import TaskAgent
    from agent_core.agents.factory import AgentConfig
    
    # Create agents - they share the same config if provided
    kwargs = {"config": config} if config else {}
    
    general_agent = GeneralAgent(**kwargs)
    rag_agent = RAGAgent(**kwargs)
    code_agent = CodeAgent(**kwargs)
    task_agent = TaskAgent(**kwargs)
    
    # Create router with all agents registered
    router = AgentRouter(
        agents={
            # Map agent type names to agent instances
            "general_chat": general_agent,
            "knowledge_search": rag_agent,
            "code_help": code_agent,
            "task_planning": task_agent,
            "task_status": task_agent,  # Task agent handles both planning and status
            "unclear": general_agent,  # Fallback to general for unclear intent
        },
        intent_mapping={
            QueryIntent.GENERAL_CHAT: "general_chat",
            QueryIntent.KNOWLEDGE_SEARCH: "knowledge_search",
            QueryIntent.CODE_HELP: "code_help",
            QueryIntent.TASK_PLANNING: "task_planning",
            QueryIntent.TASK_STATUS: "task_status",
            QueryIntent.UNCLEAR: "unclear",
        },
        default_agent="general_chat"
    )
    
    logger.info("Created default agent router with all agents registered")
    return router


def reset_agent_router() -> None:
    """Reset the global router instance. Useful for testing or reconfiguration."""
    global _agent_router
    _agent_router = None
