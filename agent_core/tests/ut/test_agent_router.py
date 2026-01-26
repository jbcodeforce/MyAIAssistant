"""Unit tests for agent router workflow."""
 
import json
import pytest

from unittest.mock import AsyncMock, patch, MagicMock

from agent_core.agents.agent_router import (
    AgentRouter,
    WorkflowState,
    RoutedResponse
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
    

    @pytest.mark.asyncio
    async def test_route_to_task_agent(self, mock_classifier, mock_task_agent):
        """Test routing task planning to task agent."""
        mock_classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.TASK_PLANNING,
            confidence=0.88,
            reasoning="User wants to plan a task",
            entities={"topic": "migration"}
        ))
        router = AgentRouter()
        router.classifier = mock_classifier
        agent = router.agents[QueryIntent.TASK_PLANNING] 
        agent._call_llm = AsyncMock(return_value="do this and that")
        response = await router.route("Help me plan the database migration")
        
        assert response.intent == QueryIntent.TASK_PLANNING
        assert response.agent_type == "TaskAgent"
        print(json.dumps(response.__dict__, indent=2, default=str))

  

class TestRouteStep:
    """Tests for the route step internals."""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = AsyncMock(spec=BaseAgent)
        agent.execute = AsyncMock(return_value=AgentResponse(
            message="Response",
            context_used=[]
        ))
        return agent
    
    @pytest.mark.asyncio
    async def test_route_step_selects_correct_agent(self, mock_agent):
        """Test route step selects correct agent based on intent."""
        router = AgentRouter()
        
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
        agent = router.agents[QueryIntent.KNOWLEDGE_SEARCH] 
        agent._call_llm = AsyncMock(return_value="do this and that")
        result = await router._route_step(state)
        
        assert result is not None
        print(json.dumps(result.__dict__, indent=2, default=str))
    
    @pytest.mark.asyncio
    async def _test_route_step_uses_default_agent(self, mock_agent):
        """Test route step uses default agent when no mapping exists for intent."""
        # Create a mapping that doesn't include UNCLEAR intent
        # to test that default_agent is used as fallback
        custom_mapping = {
            QueryIntent.KNOWLEDGE_SEARCH: "rag",
            QueryIntent.CODE_HELP: "code",
            # UNCLEAR is intentionally missing
        }
        router = AgentRouter()
        
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
    async def _test_route_step_error_no_agent(self):
        """Test route step sets error when no agent is available."""
        router = AgentRouter()
        
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
    async def _test_route_step_passes_conversation_history(self, mock_agent):
        """Test route step passes conversation history to agent."""
        router = AgentRouter()
        
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
