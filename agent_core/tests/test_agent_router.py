"""Unit tests for agent router workflow."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agent_core.agents.agent_router import (
    AgentRouter,
    WorkflowState,
    RoutedResponse,
    get_agent_router,
    _agent_router,
)
from agent_core.agents.query_classifier import (
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
)
from agent_core.agents.base_agent import BaseAgent, AgentResponse


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""
    
    def test_create_state(self):
        """Test creating workflow state."""
        state = WorkflowState(
            query="Test query",
            conversation_history=[{"role": "user", "content": "Hello"}],
            context={"task_id": 123}
        )
        
        assert state.query == "Test query"
        assert len(state.conversation_history) == 1
        assert state.context["task_id"] == 123
        assert state.classification is None
        assert state.agent_response is None
        assert state.error is None
    
    def test_create_minimal_state(self):
        """Test creating state with defaults."""
        state = WorkflowState(query="Test")
        
        assert state.query == "Test"
        assert state.conversation_history == []
        assert state.context == {}
    
    def test_state_with_classification(self):
        """Test state with classification result."""
        classification = ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.9,
            reasoning="Test reasoning",
            entities={"topic": "auth"}
        )
        state = WorkflowState(
            query="Test",
            classification=classification
        )
        
        assert state.classification.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert state.classification.confidence == 0.9
    
    def test_state_with_agent_response(self):
        """Test state with agent response."""
        agent_response = AgentResponse(
            message="Test response",
            context_used=[],
            model="gpt-4",
            provider="openai",
            agent_type="rag"
        )
        state = WorkflowState(
            query="Test",
            agent_response=agent_response
        )
        
        assert state.agent_response.message == "Test response"
        assert state.agent_response.agent_type == "rag"
    
    def test_state_with_error(self):
        """Test state with error."""
        state = WorkflowState(
            query="Test",
            error="Something went wrong"
        )
        
        assert state.error == "Something went wrong"


class TestRoutedResponse:
    """Tests for RoutedResponse dataclass."""
    
    def test_create_response(self):
        """Test creating routed response."""
        response = RoutedResponse(
            message="Test response",
            context_used=[{"title": "Doc1", "uri": "/doc1"}],
            model="gpt-4",
            provider="openai",
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.92,
            agent_type="rag",
            classification_reasoning="Knowledge search detected"
        )
        
        assert response.message == "Test response"
        assert len(response.context_used) == 1
        assert response.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert response.confidence == 0.92
        assert response.agent_type == "rag"
    
    def test_response_with_metadata(self):
        """Test response with metadata."""
        response = RoutedResponse(
            message="Test",
            context_used=[],
            model="gpt-4",
            provider="openai",
            intent=QueryIntent.CODE_HELP,
            confidence=0.95,
            agent_type="code",
            classification_reasoning="Code help",
            metadata={"entities": {"language": "python"}}
        )
        
        assert response.metadata["entities"]["language"] == "python"
    
    def test_response_default_metadata(self):
        """Test response with default empty metadata."""
        response = RoutedResponse(
            message="Test",
            context_used=[],
            model="gpt-4",
            provider="openai",
            intent=QueryIntent.GENERAL_CHAT,
            confidence=0.8,
            agent_type="general",
            classification_reasoning="General chat"
        )
        
        assert response.metadata == {}


class TestAgentRouter:
    """Tests for AgentRouter class."""
    
    @pytest.fixture
    def mock_classifier(self):
        """Create a mock query classifier."""
        classifier = AsyncMock(spec=QueryClassifier)
        return classifier
    
    @pytest.fixture
    def mock_rag_agent(self):
        """Create a mock RAG agent."""
        agent = AsyncMock(spec=BaseAgent)
        agent.agent_type = "rag"
        agent.execute = AsyncMock(return_value=AgentResponse(
            message="Found relevant documents",
            context_used=[{"title": "Doc1", "uri": "/doc1", "score": 0.9, "snippet": "..."}],
            model="gpt-4",
            provider="openai",
            agent_type="rag",
            metadata={"results_count": 3}
        ))
        return agent
    
    @pytest.fixture
    def mock_task_agent(self):
        """Create a mock task agent."""
        agent = AsyncMock(spec=BaseAgent)
        agent.agent_type = "task"
        agent.execute = AsyncMock(return_value=AgentResponse(
            message="Here's your task breakdown",
            context_used=[],
            model="gpt-4",
            provider="openai",
            agent_type="task",
            metadata={}
        ))
        return agent
    
    @pytest.fixture
    def mock_general_agent(self):
        """Create a mock general agent."""
        agent = AsyncMock(spec=BaseAgent)
        agent.agent_type = "general"
        agent.execute = AsyncMock(return_value=AgentResponse(
            message="General response",
            context_used=[],
            model="gpt-4",
            provider="openai",
            agent_type="general",
            metadata={}
        ))
        return agent
    
    @pytest.fixture
    def mock_code_agent(self):
        """Create a mock code agent."""
        agent = AsyncMock(spec=BaseAgent)
        agent.agent_type = "code"
        agent.execute = AsyncMock(return_value=AgentResponse(
            message="Here's the code solution",
            context_used=[],
            model="gpt-4",
            provider="openai",
            agent_type="code",
            metadata={}
        ))
        return agent
    
    @pytest.fixture
    def router(self, mock_classifier, mock_rag_agent, mock_task_agent, 
               mock_general_agent, mock_code_agent):
        """Create router with mock agents."""
        return AgentRouter(
            classifier=mock_classifier,
            agents={
                "rag": mock_rag_agent,
                "task": mock_task_agent,
                "general": mock_general_agent,
                "code": mock_code_agent,
            }
        )

    @pytest.mark.asyncio
    async def test_route_to_rag_agent(self, router, mock_classifier, mock_rag_agent):
        """Test routing knowledge search to RAG agent."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.92,
            reasoning="User asking about documents",
            entities={"topic": "authentication"}
        ))
        
        response = await router.route("What does our doc say about auth?")
        
        assert response.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert response.agent_type == "rag"
        assert "Found relevant documents" in response.message
        mock_rag_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_task_agent(self, router, mock_classifier, mock_task_agent):
        """Test routing task planning to task agent."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.TASK_PLANNING,
            confidence=0.88,
            reasoning="User wants to plan a task",
            entities={"topic": "migration"}
        ))
        
        response = await router.route("Help me plan the database migration")
        
        assert response.intent == QueryIntent.TASK_PLANNING
        assert response.agent_type == "task"
        mock_task_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_code_agent(self, router, mock_classifier, mock_code_agent):
        """Test routing code help to code agent."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.CODE_HELP,
            confidence=0.95,
            reasoning="User needs programming help",
            entities={"topic": "FastAPI"}
        ))
        
        response = await router.route("How do I implement JWT in FastAPI?")
        
        assert response.intent == QueryIntent.CODE_HELP
        assert response.agent_type == "code"
        mock_code_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_general_agent(self, router, mock_classifier, mock_general_agent):
        """Test routing general chat to general agent."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.GENERAL_CHAT,
            confidence=0.75,
            reasoning="General conversation",
            entities={}
        ))
        
        response = await router.route("Hello, how are you?")
        
        assert response.intent == QueryIntent.GENERAL_CHAT
        assert response.agent_type == "general"
        mock_general_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_unclear_to_general(self, router, mock_classifier, mock_general_agent):
        """Test that unclear intent routes to general agent."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.UNCLEAR,
            confidence=0.4,
            reasoning="Query is ambiguous",
            entities={}
        ))
        
        response = await router.route("xyz")
        
        assert response.intent == QueryIntent.UNCLEAR
        assert response.agent_type == "general"

    @pytest.mark.asyncio
    async def test_route_task_status(self, router, mock_classifier, mock_task_agent):
        """Test that task status routes to task agent."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.TASK_STATUS,
            confidence=0.85,
            reasoning="User asking about task status",
            entities={}
        ))
        
        response = await router.route("What's the status of my tasks?")
        
        assert response.intent == QueryIntent.TASK_STATUS
        assert response.agent_type == "task"

    @pytest.mark.asyncio
    async def test_route_with_force_intent(self, router, mock_classifier, mock_rag_agent):
        """Test forcing a specific intent bypasses classification."""
        response = await router.route(
            "Just a query",
            force_intent=QueryIntent.KNOWLEDGE_SEARCH
        )
        
        # Classification should not be called
        mock_classifier.classify.assert_not_called()
        assert response.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert response.confidence == 1.0
        mock_rag_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_with_conversation_history(self, router, mock_classifier, mock_rag_agent):
        """Test routing with conversation context."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.9,
            reasoning="Follow-up question",
            entities={}
        ))
        
        history = [
            {"role": "user", "content": "What about OAuth?"},
            {"role": "assistant", "content": "OAuth is..."}
        ]
        
        response = await router.route(
            "Tell me more about the implementation",
            conversation_history=history
        )
        
        # Verify history was passed to classifier
        mock_classifier.classify.assert_called_once()
        call_args = mock_classifier.classify.call_args
        # Check positional args (query, conversation_context)
        assert call_args[0][0] == "Tell me more about the implementation"
        assert call_args[0][1] == history

    @pytest.mark.asyncio
    async def test_route_with_context(self, router, mock_classifier, mock_task_agent):
        """Test routing with additional context."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.TASK_PLANNING,
            confidence=0.9,
            reasoning="Task planning with context",
            entities={}
        ))
        
        context = {
            "task_title": "Database Migration",
            "task_description": "Upgrade PostgreSQL"
        }
        
        response = await router.route(
            "Help me with this task",
            context=context
        )
        
        # Verify context was passed to agent
        call_args = mock_task_agent.execute.call_args
        assert "task_title" in call_args[1]["context"]

    @pytest.mark.asyncio
    async def test_route_handles_classification_error(self, router, mock_classifier, mock_general_agent):
        """Test handling classification errors - should fall back to general chat."""
        mock_classifier.classify = AsyncMock(side_effect=Exception("API Error"))
        
        response = await router.route("Test query")
        
        # Should fall back to general chat
        assert response.intent == QueryIntent.GENERAL_CHAT
        mock_general_agent.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_handles_agent_error(self, router, mock_classifier, mock_rag_agent):
        """Test handling agent execution errors."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.9,
            reasoning="Test",
            entities={}
        ))
        mock_rag_agent.execute = AsyncMock(side_effect=Exception("Agent Error"))
        
        response = await router.route("Search query")
        
        # Should return error response
        assert "error" in response.message.lower()
        assert response.agent_type == "error"

    @pytest.mark.asyncio
    async def test_response_includes_classification_metadata(self, router, mock_classifier, mock_rag_agent):
        """Test that response includes classification metadata."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.92,
            reasoning="User is searching for information",
            entities={"topic": "auth", "keywords": ["oauth"]},
            suggested_context="Security policies might help"
        ))
        
        response = await router.route("Search for OAuth docs")
        
        assert response.classification_reasoning == "User is searching for information"
        assert response.metadata.get("entities") == {"topic": "auth", "keywords": ["oauth"]}
        assert response.metadata.get("suggested_context") == "Security policies might help"

    @pytest.mark.asyncio
    async def test_route_no_classifier_configured(self):
        """Test routing without a classifier returns error."""
        router = AgentRouter(classifier=None, agents={})
        
        response = await router.route("Test query")
        
        assert response.agent_type == "error"
        assert "No classifier configured" in response.message

    @pytest.mark.asyncio
    async def test_route_no_agent_for_intent(self, mock_classifier):
        """Test routing when no agent is available for the intent."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.9,
            reasoning="Test",
            entities={}
        ))
        
        # Router with no agents
        router = AgentRouter(classifier=mock_classifier, agents={})
        
        response = await router.route("Test query")
        
        assert response.agent_type == "error"
        assert "No agent available" in response.message


class TestAgentRouterIntentMapping:
    """Tests for intent to agent mapping."""
    
    def test_default_intent_mapping(self):
        """Test default intent to agent mapping."""
        router = AgentRouter()
        
        assert router.intent_mapping[QueryIntent.KNOWLEDGE_SEARCH] == "rag"
        assert router.intent_mapping[QueryIntent.TASK_PLANNING] == "task"
        assert router.intent_mapping[QueryIntent.TASK_STATUS] == "task"
        assert router.intent_mapping[QueryIntent.CODE_HELP] == "code"
        assert router.intent_mapping[QueryIntent.GENERAL_CHAT] == "general"
        assert router.intent_mapping[QueryIntent.UNCLEAR] == "general"
    
    def test_custom_intent_mapping(self):
        """Test custom intent mapping."""
        custom_mapping = {
            QueryIntent.KNOWLEDGE_SEARCH: "custom_rag",
            QueryIntent.CODE_HELP: "custom_code",
        }
        router = AgentRouter(intent_mapping=custom_mapping)
        
        assert router.intent_mapping[QueryIntent.KNOWLEDGE_SEARCH] == "custom_rag"
        assert router.intent_mapping[QueryIntent.CODE_HELP] == "custom_code"
    
    def test_default_agent_setting(self):
        """Test default agent setting."""
        router = AgentRouter(default_agent="fallback")
        
        assert router.default_agent == "fallback"


class TestAgentRouterManagement:
    """Tests for agent management methods."""
    
    @pytest.fixture
    def router(self):
        """Create a basic router with mock agents."""
        mock_rag = MagicMock(spec=BaseAgent)
        mock_general = MagicMock(spec=BaseAgent)
        return AgentRouter(
            agents={"rag": mock_rag, "general": mock_general}
        )
    
    def test_get_agent(self, router):
        """Test getting an agent by type."""
        agent = router.get_agent("rag")
        assert agent is not None
    
    def test_get_agent_not_found(self, router):
        """Test getting non-existent agent."""
        agent = router.get_agent("nonexistent")
        assert agent is None
    
    def test_register_agent(self, router):
        """Test registering a new agent."""
        mock_agent = MagicMock(spec=BaseAgent)
        router.register_agent("custom", mock_agent)
        
        assert router.get_agent("custom") is mock_agent
    
    def test_register_agent_replaces_existing(self, router):
        """Test that registering replaces existing agent."""
        original = router.get_agent("rag")
        new_agent = MagicMock(spec=BaseAgent)
        router.register_agent("rag", new_agent)
        
        assert router.get_agent("rag") is new_agent
        assert router.get_agent("rag") is not original
    
    def test_add_intent_mapping(self, router):
        """Test adding intent mapping."""
        router.add_intent_mapping(QueryIntent.TASK_STATUS, "custom")
        
        assert router.intent_mapping[QueryIntent.TASK_STATUS] == "custom"
    
    def test_add_intent_mapping_new_intent(self, router):
        """Test adding mapping for intent not in defaults."""
        router.add_intent_mapping(QueryIntent.UNCLEAR, "clarification_agent")
        
        assert router.intent_mapping[QueryIntent.UNCLEAR] == "clarification_agent"


class TestAgentRouterSyncRoute:
    """Tests for synchronous routing."""
    
    def test_route_sync_without_implementation(self):
        """Test that sync routing returns error when not fully implemented."""
        router = AgentRouter()
        
        response = router.route_sync("Test query", force_intent=QueryIntent.GENERAL_CHAT)
        
        assert response.agent_type == "error"
        assert "execute_sync" in response.message.lower() or "synchronous" in response.message.lower()
    
    def test_route_sync_no_classifier(self):
        """Test sync routing without classifier."""
        router = AgentRouter(classifier=None)
        
        response = router.route_sync("Test query")
        
        assert response.agent_type == "error"
        assert "classifier" in response.message.lower() or "synchronous" in response.message.lower()


class TestAgentRouterErrorHandling:
    """Tests for error response building."""
    
    def test_error_response_structure(self):
        """Test error response has correct structure."""
        router = AgentRouter()
        state = WorkflowState(query="Test", error="Test error message")
        
        response = router._error_response(state)
        
        assert response.agent_type == "error"
        assert response.intent == QueryIntent.UNCLEAR
        assert response.confidence == 0.0
        assert "Test error message" in response.message
        assert response.metadata["error"] == "Test error message"
    
    def test_error_response_empty_error(self):
        """Test error response with no error message."""
        router = AgentRouter()
        state = WorkflowState(query="Test", error=None)
        
        response = router._error_response(state)
        
        assert response.agent_type == "error"
        assert response.classification_reasoning == ""


class TestAgentRouterBuildResponse:
    """Tests for response building."""
    
    def test_build_response_includes_all_fields(self):
        """Test that build response includes all expected fields."""
        router = AgentRouter()
        
        agent_response = AgentResponse(
            message="Test message",
            context_used=[{"title": "Doc", "uri": "/doc"}],
            model="gpt-4",
            provider="openai",
            agent_type="rag",
            metadata={"extra": "data"}
        )
        
        classification = ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.95,
            reasoning="Knowledge search detected",
            entities={"topic": "test"},
            suggested_context="Additional context"
        )
        
        state = WorkflowState(
            query="Test query",
            classification=classification,
            agent_response=agent_response
        )
        
        response = router._build_response(state)
        
        assert response.message == "Test message"
        assert response.context_used == [{"title": "Doc", "uri": "/doc"}]
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert response.confidence == 0.95
        assert response.agent_type == "rag"
        assert response.classification_reasoning == "Knowledge search detected"
        assert response.metadata["extra"] == "data"
        assert response.metadata["entities"] == {"topic": "test"}
        assert response.metadata["suggested_context"] == "Additional context"


class TestGetAgentRouter:
    """Tests for the singleton getter."""
    
    def test_get_agent_router_returns_instance(self):
        """Test that get_agent_router returns an AgentRouter."""
        import agent_core.agents.agent_router as router_module
        router_module._agent_router = None
        
        router = get_agent_router()
        assert isinstance(router, AgentRouter)
        assert router.classifier is not None
    
    def test_get_agent_router_returns_same_instance(self):
        """Test singleton behavior."""
        import agent_core.agents.agent_router as router_module
        router_module._agent_router = None
        
        router1 = get_agent_router()
        router2 = get_agent_router()
        assert router1 is router2
    
    def test_get_agent_router_caches_instance(self):
        """Test that the router is cached in module variable."""
        import agent_core.agents.agent_router as router_module
        router_module._agent_router = None
        
        get_agent_router()
        
        assert router_module._agent_router is not None


class TestClassifyStep:
    """Tests for the classify step internals."""
    
    @pytest.fixture
    def mock_classifier(self):
        """Create a mock classifier."""
        classifier = AsyncMock(spec=QueryClassifier)
        classifier.classify_sync = MagicMock()
        return classifier
    
    @pytest.mark.asyncio
    async def test_classify_step_with_forced_intent(self, mock_classifier):
        """Test classify step with forced intent."""
        router = AgentRouter(classifier=mock_classifier)
        state = WorkflowState(query="Test query")
        
        result = await router._classify_step(state, force_intent=QueryIntent.CODE_HELP)
        
        assert result.classification.intent == QueryIntent.CODE_HELP
        assert result.classification.confidence == 1.0
        assert result.classification.reasoning == "Intent forced by caller"
        mock_classifier.classify.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_classify_step_calls_classifier(self, mock_classifier):
        """Test classify step calls the classifier."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.GENERAL_CHAT,
            confidence=0.8,
            reasoning="Test",
            entities={}
        ))
        
        router = AgentRouter(classifier=mock_classifier)
        state = WorkflowState(
            query="Hello",
            conversation_history=[{"role": "user", "content": "Previous"}]
        )
        
        result = await router._classify_step(state)
        
        mock_classifier.classify.assert_called_once_with(
            "Hello",
            [{"role": "user", "content": "Previous"}]
        )
        assert result.classification.intent == QueryIntent.GENERAL_CHAT
    
    def test_classify_step_sync_with_forced_intent(self, mock_classifier):
        """Test sync classify step with forced intent."""
        router = AgentRouter(classifier=mock_classifier)
        state = WorkflowState(query="Test query")
        
        result = router._classify_step_sync(state, force_intent=QueryIntent.TASK_PLANNING)
        
        assert result.classification.intent == QueryIntent.TASK_PLANNING
        assert result.classification.confidence == 1.0
        mock_classifier.classify_sync.assert_not_called()
    
    def test_classify_step_sync_calls_classifier(self, mock_classifier):
        """Test sync classify step calls the classifier."""
        mock_classifier.classify_sync = MagicMock(return_value=ClassificationResult(
            intent=QueryIntent.CODE_HELP,
            confidence=0.85,
            reasoning="Test",
            entities={}
        ))
        
        router = AgentRouter(classifier=mock_classifier)
        state = WorkflowState(query="Write code")
        
        result = router._classify_step_sync(state)
        
        mock_classifier.classify_sync.assert_called_once()
        assert result.classification.intent == QueryIntent.CODE_HELP
    
    def test_classify_step_sync_handles_error(self, mock_classifier):
        """Test sync classify step handles errors gracefully."""
        mock_classifier.classify_sync = MagicMock(side_effect=Exception("Sync error"))
        
        router = AgentRouter(classifier=mock_classifier)
        state = WorkflowState(query="Test")
        
        result = router._classify_step_sync(state)
        
        # Should fall back to general chat
        assert result.classification.intent == QueryIntent.GENERAL_CHAT
        assert result.classification.confidence == 0.5
        assert "failed" in result.classification.reasoning.lower()


class TestRouteStep:
    """Tests for the route step internals."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = AsyncMock(spec=BaseAgent)
        agent.execute = AsyncMock(return_value=AgentResponse(
            message="Response",
            context_used=[],
            model="gpt-4",
            provider="openai",
            agent_type="test"
        ))
        return agent
    
    @pytest.mark.asyncio
    async def test_route_step_selects_correct_agent(self, mock_agent):
        """Test route step selects correct agent based on intent."""
        router = AgentRouter(
            agents={"rag": mock_agent},
            intent_mapping={QueryIntent.KNOWLEDGE_SEARCH: "rag"}
        )
        
        classification = ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.9,
            reasoning="Test",
            entities={"topic": "search"}
        )
        state = WorkflowState(
            query="Search query",
            classification=classification,
            context={"user_id": 123}
        )
        
        result = await router._route_step(state)
        
        mock_agent.execute.assert_called_once()
        call_kwargs = mock_agent.execute.call_args[1]
        assert call_kwargs["query"] == "Search query"
        assert call_kwargs["context"]["entities"] == {"topic": "search"}
        assert call_kwargs["context"]["intent"] == "knowledge_search"
        assert call_kwargs["context"]["user_id"] == 123
    
    @pytest.mark.asyncio
    async def test_route_step_uses_default_agent(self, mock_agent):
        """Test route step uses default agent when no mapping exists for intent."""
        # Create a mapping that doesn't include UNCLEAR intent
        # to test that default_agent is used as fallback
        custom_mapping = {
            QueryIntent.KNOWLEDGE_SEARCH: "rag",
            QueryIntent.CODE_HELP: "code",
            # UNCLEAR is intentionally missing
        }
        router = AgentRouter(
            agents={"fallback": mock_agent},
            intent_mapping=custom_mapping,
            default_agent="fallback"
        )
        
        classification = ClassificationResult(
            intent=QueryIntent.UNCLEAR,
            confidence=0.5,
            reasoning="Test",
            entities={}
        )
        state = WorkflowState(
            query="?",
            classification=classification
        )
        
        result = await router._route_step(state)
        
        mock_agent.execute.assert_called_once()
        assert result.error is None
    
    @pytest.mark.asyncio
    async def test_route_step_error_no_agent(self):
        """Test route step sets error when no agent is available."""
        router = AgentRouter(agents={})
        
        classification = ClassificationResult(
            intent=QueryIntent.CODE_HELP,
            confidence=0.9,
            reasoning="Test",
            entities={}
        )
        state = WorkflowState(
            query="Code help",
            classification=classification
        )
        
        result = await router._route_step(state)
        
        assert result.error is not None
        assert "No agent available" in result.error
    
    @pytest.mark.asyncio
    async def test_route_step_passes_conversation_history(self, mock_agent):
        """Test route step passes conversation history to agent."""
        router = AgentRouter(
            agents={"general": mock_agent},
            intent_mapping={QueryIntent.GENERAL_CHAT: "general"}
        )
        
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"}
        ]
        
        classification = ClassificationResult(
            intent=QueryIntent.GENERAL_CHAT,
            confidence=0.9,
            reasoning="Test",
            entities={}
        )
        state = WorkflowState(
            query="How are you?",
            conversation_history=history,
            classification=classification
        )
        
        await router._route_step(state)
        
        call_kwargs = mock_agent.execute.call_args[1]
        assert call_kwargs["conversation_history"] == history
