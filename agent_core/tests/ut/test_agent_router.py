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
from agent_core.agents.base_agent import BaseAgent, AgentInput, AgentResponse

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
        """Test routing task planning to task agent.
        
        This test verifies:
        1. Classifier is called first to determine intent (via execute method)
        2. Task agent is called second to handle the task planning query
        Both are properly mocked to avoid real LLM calls.
        """
        query = "Help me plan the database migration"
        
        # Setup router
        router = AgentRouter()
        
        # Mock 1: Classifier's LLM client (called first via classifier.execute)
        classifier_llm_called = {}
        async def mock_classifier_chat_async(messages, config):
            classifier_llm_called["called"] = True
            # Verify the query is in the messages
            message_contents = " ".join([msg.content for msg in messages if msg.role == "user"])
            assert "database" in message_contents.lower() or "migration" in message_contents.lower()
            
            # Return a JSON response that will be parsed into ClassificationResult
            from agent_core.types import LLMResponse
            return LLMResponse(
                content='{"intent": "task_planning", "confidence": 0.88, "reasoning": "User wants to plan a task", "entities": {"topic": "migration"}}',
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 15, "completion_tokens": 20, "total_tokens": 35}
            )
        
        # Get the actual classifier and mock its LLM client
        classifier = router.classifier
        classifier._llm_client.chat_async = mock_classifier_chat_async
        
        # Get the actual task agent from router
        agent = router.get_agent_for_intent(QueryIntent.TASK_PLANNING)
        
        # Mock 2: Task agent's LLM client (called second via agent.execute)
        task_agent_llm_called = {}
        async def mock_task_agent_chat_async(messages, config):
            # Verify message construction occurred
            assert messages is not None
            assert isinstance(messages, list)
            # Verify the query about database migration is in the messages
            message_contents = " ".join([msg.content for msg in messages if msg.role == "user"])
            assert "database" in message_contents.lower() or "migration" in message_contents.lower()
            task_agent_llm_called["called"] = True
            
            # Return a task planning response
            from agent_core.types import LLMResponse
            return LLMResponse(
                content="Here's a plan for the database migration:\n1. Backup existing database\n2. Create migration scripts\n3. Test in staging environment\n4. Execute migration\n5. Verify data integrity",
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 20, "completion_tokens": 30, "total_tokens": 50}
            )
        agent._llm_client.chat_async = mock_task_agent_chat_async
        
        # Execute the routing
        input_data = AgentInput(query=query)
        response = await router.execute(input_data)
        
        # Verify classifier's LLM was called first
        assert classifier_llm_called.get("called", False), "Classifier's LLM should have been called first"
        
        # Verify task agent's LLM was called second
        assert task_agent_llm_called.get("called", False), "Task agent's LLM should have been called second"
        
        # Verify response structure
        assert response is not None
        assert response.intent == QueryIntent.TASK_PLANNING
        assert response.agent_type == "TaskAgent"
        assert "migration" in response.message.lower() or "database" in response.message.lower()
        assert response.confidence == 0.88

  

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
        agent = router.get_agent_for_intent(QueryIntent.KNOWLEDGE_SEARCH)
        
        # Mock the agent's LLM client
        from agent_core.types import LLMResponse
        async def mock_chat_async(messages, config):
            return LLMResponse(
                content="Here are the search results: ...",
                model=config.model,
                provider=config.provider,
                usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
            )
        agent._llm_client.chat_async = mock_chat_async
        
        result = await router._route_step(state)
        
        assert result is not None
        assert result.agent_response is not None
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
