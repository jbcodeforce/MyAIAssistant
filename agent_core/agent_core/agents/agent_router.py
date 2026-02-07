"""Agent router for query classification and routing workflow.

This module implements the main routing workflow that:
1. Classifies incoming queries
2. Routes to appropriate specialized agents
3. Orchestrates the response generation
"""

import json
import logging
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Optional, Dict, Any

from pydantic import BaseModel, Field
from agent_core.agents.agent_config import AgentConfig, LOCAL_MODEL, LOCAL_BASE_URL
from agent_core.agents.agent_factory import get_agent_factory

from agent_core.agents.base_agent import BaseAgent, AgentResponse, AgentInput
from agent_core.agents.query_classifier import (
    QueryClassifier,
    ClassificationResult,
    QueryIntent,
)
from agent_core.agents._llm_default import LLMCallable
logger = logging.getLogger(__name__)


@dataclass
class WorkflowState:
    """State passed through the routing workflow."""
    query: str
    conversation_history: list[dict] = field(default_factory=list)
    classification: Optional[ClassificationResult] = None
    agent_response: Optional[AgentResponse] = None
    context: dict = field(default_factory=dict)
    error: Optional[str] = None
    agent: Optional[BaseAgent] = None
    agent_input_data: Optional[AgentInput] = None


class RoutedResponse(AgentResponse):
    """Final response from the routing workflow."""
    intent: QueryIntent
    confidence: float
    classification_reasoning: str


class AgentRouter(BaseAgent):
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

    # Built-in default: intent name -> agent name (used when router.yaml is absent)
    _DEFAULT_ROUTER_MAPPING = {
        "knowledge_search": "GeneralAgent",
        "routing": "AgentRouter",
        "task_planning": "TaskAgent",
        "task_status": "TaskAgent",
        "code_help": "CodeAgent",
        "general_chat": "GeneralAgent",
        "unclear": "GeneralAgent",
    }
    _DEFAULT_AGENT_NAME = "GeneralAgent"

    @staticmethod
    def _load_router_config(config_dir: Optional[str]) -> Dict[str, Any]:
        """
        Load router config from config_dir/router.yaml or return built-in default.

        Returns:
            dict with "default_agent" (str) and "mapping" (dict intent_str -> agent_name).
        """
        mapping = dict(AgentRouter._DEFAULT_ROUTER_MAPPING)
        default_agent = AgentRouter._DEFAULT_AGENT_NAME
        if config_dir:
            path = Path(config_dir) / "router.yaml"
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                    default_agent = data.get("default_agent", default_agent)
                    if "mapping" in data and isinstance(data["mapping"], dict):
                        mapping = data["mapping"]
                    logger.debug(f"Loaded router config from {path}")
                except Exception as e:
                    logger.warning(f"Failed to load router config from {path}: {e}")
        return {"default_agent": default_agent, "mapping": mapping}

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_client: Optional[LLMCallable] = None,
    ):
        """
        Initialize the router.

        Loads intent -> agent mapping from config_dir/router.yaml if present,
        otherwise uses built-in default. Creates one agent instance per unique
        agent name and maps QueryIntent to agent name for routing.

        Args:
            config_dir: Optional path to agent configuration directory.
                       If None, uses AgentFactory default.
        """
        super().__init__(config=config, llm_client=llm_client)
        factory = get_agent_factory()
        router_cfg = self._load_router_config(config_dir = self._config.agent_dir)
        default_agent_name = router_cfg["default_agent"]
        mapping_raw = router_cfg["mapping"]

        self.classifier = factory.create_agent("QueryClassifier")
        self.default_agent_name = default_agent_name
        self.intent_mapping: Dict[QueryIntent, str] = {}
        for k, v in mapping_raw.items():
            try:
                intent = QueryIntent(k)
                self.intent_mapping[intent] = v
            except ValueError:
                logger.warning("Unknown intent in router config, skipping: %s", k)

        agent_names = set(self.intent_mapping.values()) | {default_agent_name}
        agent_names.discard("QueryClassifier")
        agent_names.discard("AgentRouter")
        self.agents: Dict[str, BaseAgent] = {}
        for name in agent_names:
            try:
                self.agents[name] = factory.create_agent(name)
            except ValueError as e:
                logger.warning("Cannot create agent %s: %s", name, e)

        self.default_agent = self.agents.get(default_agent_name)
        if self.default_agent is None and self.agents:
            self.default_agent = next(iter(self.agents.values()))
            logger.warning(
                "default_agent %s not in agents map, using first available",
                default_agent_name,
            )



    async def execute(
        self,
        input_data: AgentInput,
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
            query=input_data.query,
            conversation_history=input_data.conversation_history or [],
            context=input_data.context or {}
        )
        
        # Step 1: Classify the query
        state = await self._classify_step(state, force_intent)
        logger.info(f"Classification: {json.dumps(state.__dict__, indent=2, default=str)}")
        if state.error:
            return self._error_response(state)
        
        # Step 2: Route to appropriate agent
        state = await self._route_step(state)
        logger.info(f"Routing: {json.dumps(state.__dict__, indent=2, default=str)}")
        if state.error:
            return self._error_response(state)
        
        # Step 3: Build and return response
        resp=self._build_response(state)
        logger.info(f"Response: {json.dumps(resp.__dict__, indent=2, default=str)}")
        return resp

    async def route_stream(
        self,
        query: str,
        conversation_history: Optional[list[dict]] = None,
        context: Optional[dict] = None,
        force_intent: Optional[QueryIntent] = None,
    ) -> AsyncIterator[str]:
        """
        Route a query and stream response content chunk by chunk.

        Runs the same classification and routing as route(); then yields
        chunks from the selected agent's execute_stream (or full message if not available).
        """
        state = WorkflowState(
            query=query,
            conversation_history=conversation_history or [],
            context=context or {},
        )
        state = await self._classify_step(state, force_intent)
        if state.error:
            yield f"I encountered an error: {state.error}"
            return
        state = await self._route_step_prepare(state)
        if state.error:
            yield f"I encountered an error: {state.error}"
            return
        agent = state.agent
        input_data = state.agent_input_data
        if not agent or not input_data:
            yield "No agent available for this request."
            return
        execute_stream = getattr(agent, "execute_stream", None)
        if callable(execute_stream):
            async for chunk in execute_stream(input_data):
                yield chunk
        else:
            try:
                response = await agent.execute(input_data)
                if response.message:
                    yield response.message
            except Exception as e:
                logger.error("Agent execution failed: %s", e)
                yield f"Agent execution failed: {str(e)}"

    async def _route_step_prepare(self, state: WorkflowState) -> WorkflowState:
        """Select agent and build input without executing. Sets state.agent and state.agent_input_data."""
        intent = state.classification.intent
        agent_name = self.intent_mapping.get(intent, self.default_agent_name)
        agent = self.agents.get(agent_name) or self.default_agent

        if not agent:
            state.error = f"No agent available for intent: {intent.value} (agent: {agent_name})"
            return state

        logger.info("Routing to %s agent (stream)", agent_name)

        agent_context = {
            **state.context,
            "entities": state.classification.entities,
            "intent": intent.value,
        }

        try:
            input_data = AgentInput(
                query=state.query,
                conversation_history=state.conversation_history,
                context=agent_context,
            )
            cfg = getattr(agent, "_config", None)
            if cfg is not None and getattr(cfg, "use_rag", False):
                input_data.use_rag = True
            elif intent in (
                QueryIntent.KNOWLEDGE_SEARCH,
                QueryIntent.TASK_STATUS,
                QueryIntent.TASK_PLANNING,
                QueryIntent.CODE_HELP,
            ):
                input_data.use_rag = True
            state.agent = agent
            state.agent_input_data = input_data
        except Exception as e:
            logger.error("Route prepare failed: %s", e)
            state.error = str(e)

        return state

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
        agent_name = self.intent_mapping.get(intent, self.default_agent_name)
        agent = self.agents.get(agent_name) or self.default_agent

        if not agent:
            state.error = f"No agent available for intent: {intent.value} (agent: {agent_name})"
            return state

        logger.info("Routing to %s agent", agent_name)

        agent_context = {
            **state.context,
            "entities": state.classification.entities,
            "intent": intent.value,
        }

        try:
            input_data = AgentInput(
                query=state.query,
                conversation_history=state.conversation_history,
                context=agent_context,
            )
            cfg = getattr(agent, "_config", None)
            if cfg is not None and getattr(cfg, "use_rag", False):
                input_data.use_rag = True
            elif intent in (
                QueryIntent.KNOWLEDGE_SEARCH,
                QueryIntent.TASK_STATUS,
                QueryIntent.TASK_PLANNING,
                QueryIntent.CODE_HELP,
            ):
                input_data.use_rag = True
            state.agent_response = await agent.execute(input_data)
        except Exception as e:
            logger.error("Agent execution failed: %s", e)
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
        """Get a specific agent by type (agent name)."""
        return self.agents.get(agent_type)

    def get_agent_for_intent(self, intent: QueryIntent) -> Optional[BaseAgent]:
        """Get the agent that handles the given intent."""
        agent_name = self.intent_mapping.get(intent, self.default_agent_name)
        return self.agents.get(agent_name) or self.default_agent

    def register_agent(self, agent_type: str, agent: BaseAgent) -> None:
        """Register a new agent or replace an existing one."""
        self.agents[agent_type] = agent
        logger.info(f"Registered agent: {agent_type}")

    def add_intent_mapping(self, intent: QueryIntent, agent_type: str) -> None:
        """Add or update intent to agent mapping."""
        self.intent_mapping[intent] = agent_type

