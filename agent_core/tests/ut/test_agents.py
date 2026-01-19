"""Tests for agent framework components."""

import pytest
from unittest.mock import AsyncMock, MagicMock
import json

from agent_core.agents import (
    BaseAgent,
    AgentResponse,
    AgentInput,
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
    CLASSIFICATION_PROMPT,
    AgentRouter,
    WorkflowState,
    RoutedResponse,
)
from agent_core import LLMResponse
from agent_core.agents.factory import AgentFactory


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""
    
    def test_create_response(self):
        """Test creating an agent response."""
        response = AgentResponse(
            message="Test response",
            context_used=[{"title": "Doc1"}],
            model="gpt-4",
            provider="openai",
            agent_type="test",
            metadata={"key": "value"}
        )
        
        assert response.message == "Test response"
        assert len(response.context_used) == 1
        assert response.model == "gpt-4"
        assert response.agent_type == "test"
    
    def test_create_minimal_response(self):
        """Test creating response with defaults."""
        response = AgentResponse(message="Test")
        
        assert response.message == "Test"
        assert response.context_used == []
        assert response.model == ""


class TestBaseAgent:
    """Tests for BaseAgent class."""
    
    def test_create_base_agent(self):
        """Test creating a base agent."""
        factory = AgentFactory()
        agent = factory.create_agent()
        assert agent is not None
        assert agent._config is not None
        assert agent._config.model == "gpt-oss:20b"
        assert agent._config.api_key is None
        assert agent._config.max_tokens == 2048
        assert agent._config.temperature == 0.7
        assert agent._config.timeout == 60.0
        assert agent._system_prompt is not None
        assert "helpful ai assistant" in agent._system_prompt.lower()

    @pytest.mark.asyncio
    async def test_execute_agent(self):
        """Test executing a base agent."""
        factory = AgentFactory()
        agent = factory.create_agent()
        
        # Mock the _call_llm method to return a fake response
        agent._call_llm = AsyncMock(return_value="Python is a high-level programming language known for its simplicity and readability.")
        
        response = await agent.execute(AgentInput(query="What is Python?"))
        assert response is not None
        assert response.message is not None
        assert response.model is not None
        assert response.provider is not None
        assert response.agent_type is not None
        assert response.context_used is not None
        assert response.metadata is not None
        assert "python is a high-level programming language" in response.message.lower()
        
        # Verify _call_llm was called
        agent._call_llm.assert_called_once()

    async def test_execute_agent_with_rag(self):
        """Test executing a base agent with RAG."""
        factory = AgentFactory()
        agent = factory.create_agent()
        
        # Mock the _call_llm method to return a fake response
        agent._call_llm = AsyncMock(return_value="Python is a high-level programming language known for its simplicity and readability.")
        
        response = await agent.execute(AgentInput(query="What is Python?", use_rag=True))   
        assert response is not None
        assert response.message is not None
        assert response.model is not None
        assert response.provider is not None
        assert response.agent_type is not None
        assert response.context_used is not None
        assert response.metadata is not None
        assert "python is a high-level programming language" in response.message.lower()

class TestQueryIntent:
    """Tests for QueryIntent enum."""
    
    def test_intent_values(self):
        """Test that all expected intents exist."""
        assert QueryIntent.KNOWLEDGE_SEARCH == "knowledge_search"
        assert QueryIntent.TASK_PLANNING == "task_planning"
        assert QueryIntent.CODE_HELP == "code_help"
        assert QueryIntent.GENERAL_CHAT == "general_chat"
    
    def test_intent_from_string(self):
        """Test creating intent from string value."""
        intent = QueryIntent("knowledge_search")
        assert intent == QueryIntent.KNOWLEDGE_SEARCH


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""
    
    def test_create_result(self):
        """Test creating a classification result."""
        result = ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.95,
            reasoning="Query asks about finding documents",
            entities={"topic": "auth"}
        )
        
        assert result.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert result.confidence == 0.95


class TestClassificationPrompt:
    """Tests for the classification prompt."""
    
    def test_prompt_contains_all_intents(self):
        """Test that prompt includes all intent types."""
        assert "knowledge_search" in CLASSIFICATION_PROMPT
        assert "task_planning" in CLASSIFICATION_PROMPT
        assert "code_help" in CLASSIFICATION_PROMPT
        assert "general_chat" in CLASSIFICATION_PROMPT


class TestQueryClassifier:
    """Tests for QueryClassifier class."""
    
    @pytest.fixture
    def classifier(self):
        """Create a query classifier for testing."""
        return QueryClassifier(
            provider="openai",
            model="gpt-4",
            api_key="test-key",
            max_tokens=500,
            temperature=0.1
        )
    
    @pytest.fixture
    def mock_llm_response(self):
        """Mock response for classification."""
        return json.dumps({
            "intent": "knowledge_search",
            "confidence": 0.92,
            "reasoning": "User is asking about documents",
            "entities": {"topic": "auth"}
        })
    
    @pytest.mark.asyncio
    async def test_classify_returns_result(self, classifier, mock_llm_response):
        """Test classifying a query."""
        classifier._llm_client.chat_async = AsyncMock(
            return_value=LLMResponse(
                content=mock_llm_response,
                model="gpt-4",
                provider="openai"
            )
        )
        
        result = await classifier.classify("What docs do we have on OAuth?")
        
        assert result.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert result.confidence == 0.92
    
    @pytest.mark.asyncio
    async def test_classify_handles_error(self, classifier):
        """Test that classification handles errors gracefully."""
        classifier._llm_client.chat_async = AsyncMock(side_effect=Exception("API Error"))
        
        result = await classifier.classify("Any query")
        
        assert result.intent == QueryIntent.GENERAL_CHAT
        assert result.confidence == 0.5


class TestWorkflowState:
    """Tests for WorkflowState dataclass."""
    
    def test_create_state(self):
        """Test creating workflow state."""
        state = WorkflowState(query="Test query")
        
        assert state.query == "Test query"
        assert state.conversation_history == []
        assert state.classification is None


class TestRoutedResponse:
    """Tests for RoutedResponse dataclass."""
    
    def test_create_response(self):
        """Test creating a routed response."""
        response = RoutedResponse(
            message="Response",
            context_used=[],
            model="gpt-4",
            provider="openai",
            intent=QueryIntent.GENERAL_CHAT,
            confidence=0.9,
            agent_type="general",
            classification_reasoning="General query"
        )
        
        assert response.message == "Response"
        assert response.intent == QueryIntent.GENERAL_CHAT


class TestAgentRouter:
    """Tests for AgentRouter class."""
    
    @pytest.fixture
    def mock_classifier(self):
        """Create a mock classifier."""
        classifier = MagicMock()
        classifier.classify = AsyncMock(return_value=ClassificationResult(
            intent=QueryIntent.GENERAL_CHAT,
            confidence=0.9,
            reasoning="General query",
            entities={}
        ))
        return classifier
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        agent = MagicMock(spec=BaseAgent)
        agent.execute = AsyncMock(return_value=AgentResponse(
            message="Response from agent",
            model="gpt-4",
            provider="openai",
            agent_type="general"
        ))
        return agent
    
    @pytest.fixture
    def router(self, mock_classifier, mock_agent):
        """Create a router with mock dependencies."""
        return AgentRouter(
            classifier=mock_classifier,
            agents={"general": mock_agent},
            intent_mapping={
                QueryIntent.GENERAL_CHAT: "general",
                QueryIntent.UNCLEAR: "general",
            },
            default_agent="general"
        )
    
    @pytest.mark.asyncio
    async def test_route_returns_response(self, router):
        """Test routing a query."""
        response = await router.route("Hello!")
        
        assert response.message == "Response from agent"
        assert response.agent_type == "general"
    
    @pytest.mark.asyncio
    async def test_route_with_force_intent(self, router, mock_agent):
        """Test routing with forced intent."""
        response = await router.route(
            "Hello!",
            force_intent=QueryIntent.GENERAL_CHAT
        )
        
        assert response.confidence == 1.0
        mock_agent.execute.assert_called_once()
    
    def test_register_agent(self, router):
        """Test registering a new agent."""
        new_agent = MagicMock(spec=BaseAgent)
        router.register_agent("custom", new_agent)
        
        assert router.get_agent("custom") is new_agent
    
    def test_add_intent_mapping(self, router):
        """Test adding intent mapping."""
        router.add_intent_mapping(QueryIntent.CODE_HELP, "custom")
        
        assert router.intent_mapping[QueryIntent.CODE_HELP] == "custom"


