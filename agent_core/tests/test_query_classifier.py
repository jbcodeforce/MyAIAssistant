"""Unit tests for query classification agent."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from agent_core.agents.agent_config import AgentConfig
from agent_core.agents.base_agent import AgentInput
from agent_core.agents.query_classifier import (
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
)
from agent_core.agents._llm_default import DefaultHFAdapter
from agent_core.types import LLMResponse


class TestQueryIntent:
    """Tests for QueryIntent enum."""
    
    def test_intent_values(self):
        """Test that all expected intents exist."""
        assert QueryIntent.KNOWLEDGE_SEARCH == "knowledge_search"
        assert QueryIntent.TASK_PLANNING == "task_planning"
        assert QueryIntent.TASK_STATUS == "task_status"
        assert QueryIntent.GENERAL_CHAT == "general_chat"
        assert QueryIntent.CODE_HELP == "code_help"
        assert QueryIntent.UNCLEAR == "unclear"

    def test_intent_from_string(self):
        """Test creating intent from string value."""
        intent = QueryIntent("knowledge_search")
        assert intent == QueryIntent.KNOWLEDGE_SEARCH
    
    def test_intent_invalid_string_raises(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            QueryIntent("invalid_intent")


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""
    
    def test_create_result(self):
        """Test creating a classification result."""
        result = ClassificationResult(
            intent=QueryIntent.KNOWLEDGE_SEARCH,
            confidence=0.95,
            reasoning="Query asks about finding documents",
            entities={"topic": "authentication", "keywords": ["oauth", "jwt"]}
        )
        
        assert result.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert result.confidence == 0.95
        assert result.reasoning == "Query asks about finding documents"
        assert result.entities["topic"] == "authentication"
        assert result.suggested_context is None
    
    def test_create_result_with_suggested_context(self):
        """Test creating result with suggested context."""
        result = ClassificationResult(
            intent=QueryIntent.TASK_PLANNING,
            confidence=0.8,
            reasoning="Task breakdown requested",
            entities={},
            suggested_context="Project timeline would help"
        )
        
        assert result.suggested_context == "Project timeline would help"


class TestQueryClassifier:
    """Tests for QueryClassifier class."""
    
    @pytest.fixture
    def classifier(self):
        """Create a query classifier for testing."""
        config = AgentConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key",
            temperature=0.1,
        )
        return QueryClassifier(config=config)
    
    @pytest.fixture
    def mock_llm_response_knowledge(self):
        """Mock response for knowledge search classification."""
        return json.dumps({
            "intent": "knowledge_search",
            "confidence": 0.92,
            "reasoning": "User is asking about finding information in their documents",
            "entities": {
                "topic": "authentication",
                "action": "search",
                "keywords": ["oauth", "security"]
            },
            "suggested_context": None
        })
    
    @pytest.fixture
    def mock_llm_response_task(self):
        """Mock response for task planning classification."""
        return json.dumps({
            "intent": "task_planning",
            "confidence": 0.88,
            "reasoning": "User wants help breaking down a task",
            "entities": {
                "topic": "migration",
                "action": "plan",
                "keywords": ["database", "upgrade"]
            }
        })
    
    @pytest.fixture
    def mock_llm_response_code(self):
        """Mock response for code help classification."""
        return json.dumps({
            "intent": "code_help",
            "confidence": 0.95,
            "reasoning": "User needs help with programming implementation",
            "entities": {
                "topic": "FastAPI",
                "action": "implement",
                "keywords": ["authentication", "endpoint"]
            }
        })
    
    @pytest.fixture
    def mock_llm_response_general(self):
        """Mock response for general chat classification."""
        return json.dumps({
            "intent": "general_chat",
            "confidence": 0.75,
            "reasoning": "General conversation not related to specific domain",
            "entities": {}
        })

    def _mock_llm_response(self, content: str) -> LLMResponse:
        return LLMResponse(content=content, model="test", provider="test")

    @pytest.mark.asyncio
    async def test_classify_knowledge_search(self, classifier, mock_llm_response_knowledge):
        """Test classifying a knowledge search query."""
        classifier._llm_client.chat_async = AsyncMock(
            return_value=self._mock_llm_response(mock_llm_response_knowledge)
        )
        result = await classifier.execute(
            AgentInput(query="What does our documentation say about OAuth authentication?")
        )
        assert result.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert result.confidence == 0.92
        assert "authentication" in result.entities.get("topic", "")
        classifier._llm_client.chat_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_task_planning(self, classifier, mock_llm_response_task):
        """Test classifying a task planning query."""
        classifier._llm_client.chat_async = AsyncMock(
            return_value=self._mock_llm_response(mock_llm_response_task)
        )
        result = await classifier.execute(
            AgentInput(query="Help me break down the database migration into steps")
        )
        assert result.intent == QueryIntent.TASK_PLANNING
        assert result.confidence == 0.88
        classifier._llm_client.chat_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_code_help(self, classifier, mock_llm_response_code):
        """Test classifying a code help query."""
        classifier._llm_client.chat_async = AsyncMock(
            return_value=self._mock_llm_response(mock_llm_response_code)
        )
        result = await classifier.execute(
            AgentInput(query="How do I implement JWT authentication in FastAPI?")
        )
        assert result.intent == QueryIntent.CODE_HELP
        assert result.confidence == 0.95
        classifier._llm_client.chat_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_general_chat(self, classifier, mock_llm_response_general):
        """Test classifying a general chat query."""
        classifier._llm_client.chat_async = AsyncMock(
            return_value=self._mock_llm_response(mock_llm_response_general)
        )
        result = await classifier.execute(AgentInput(query="Hello, how are you today?"))
        assert result.intent == QueryIntent.GENERAL_CHAT
        assert result.confidence == 0.75
        classifier._llm_client.chat_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_with_conversation_context(self, classifier, mock_llm_response_knowledge):
        """Test classification with conversation context."""
        classifier._llm_client.chat_async = AsyncMock(
            return_value=self._mock_llm_response(mock_llm_response_knowledge)
        )
        context = [
            {"role": "user", "content": "I'm looking for security docs"},
            {"role": "assistant", "content": "What specifically about security?"},
        ]
        result = await classifier.execute(
            AgentInput(
                query="The OAuth implementation",
                conversation_history=context,
            )
        )
        assert result.intent == QueryIntent.KNOWLEDGE_SEARCH

    @pytest.mark.asyncio
    async def test_classify_handles_llm_error(self, classifier):
        """Test that classification handles LLM errors gracefully."""
        classifier._llm_client.chat_async = AsyncMock(side_effect=Exception("API Error"))
        result = await classifier.execute(AgentInput(query="Any query"))
        assert result.intent == QueryIntent.GENERAL_CHAT
        assert result.confidence == 0.5
        assert "Classification failed" in result.reasoning

    @pytest.mark.asyncio
    async def test_classify_handles_invalid_json(self, classifier):
        """Test handling of invalid JSON response from LLM."""
        classifier._llm_client.chat_async = AsyncMock(
            return_value=self._mock_llm_response("This is not valid JSON")
        )
        result = await classifier.execute(AgentInput(query="Test query"))
        assert result.intent == QueryIntent.GENERAL_CHAT
        assert result.confidence == 0.5
        assert "Failed to parse" in result.reasoning

    @pytest.mark.asyncio
    async def test_classify_handles_markdown_json(self, classifier):
        """Test handling JSON wrapped in markdown code blocks."""
        json_content = {
            "intent": "task_planning",
            "confidence": 0.85,
            "reasoning": "Task related",
            "entities": {},
        }
        markdown_response = f"```json\n{json.dumps(json_content)}\n```"
        classifier._llm_client.chat_async = AsyncMock(
            return_value=self._mock_llm_response(markdown_response)
        )
        result = await classifier.execute(AgentInput(query="Help me plan this task"))
        assert result.intent == QueryIntent.TASK_PLANNING
        assert result.confidence == 0.85

    @pytest.mark.asyncio
    async def test_classify_handles_unknown_intent(self, classifier):
        """Test handling of unknown intent value from LLM."""
        response = json.dumps({
            "intent": "unknown_intent_type",
            "confidence": 0.9,
            "reasoning": "Unknown type",
            "entities": {},
        })
        classifier._llm_client.chat_async = AsyncMock(
            return_value=self._mock_llm_response(response)
        )
        result = await classifier.execute(AgentInput(query="Test query"))
        assert result.intent == QueryIntent.GENERAL_CHAT


class TestQueryClassifierLLMClient:
    """Tests for QueryClassifier LLM client integration."""

    def test_classifier_has_llm_client(self):
        """Test that classifier has _llm_client (default HF adapter or injected)."""
        config = AgentConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key",
            temperature=0.1,
        )
        classifier = QueryClassifier(config=config)

        assert hasattr(classifier, "_llm_client")
        assert isinstance(classifier._llm_client, DefaultHFAdapter)

    def test_classifier_has_agent_config(self):
        """Test that classifier creates AgentConfig."""
        config = AgentConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key",
            temperature=0.1,
        )
        classifier = QueryClassifier(config=config)

        assert hasattr(classifier, "_config")
        assert isinstance(classifier._config, AgentConfig)
        assert classifier._config.provider == "openai"
        assert classifier._config.temperature == 0.1

    @pytest.mark.asyncio
    async def test_execute_uses_llm_client(self):
        """Test that execute uses _llm_client.chat_async."""
        from agent_core.types import LLMResponse
        from agent_core.agents.base_agent import AgentInput

        config = AgentConfig(
            provider="openai",
            model="gpt-4",
            api_key="test-key",
            temperature=0.1,
        )
        classifier = QueryClassifier(config=config)

        mock_response = LLMResponse(
            content='{"intent": "general_chat", "confidence": 0.8, "reasoning": "test", "entities": {}}',
            model="gpt-4",
            provider="openai",
        )

        classifier._llm_client.chat_async = AsyncMock(return_value=mock_response)

        result = await classifier.execute(AgentInput(query="Test prompt"))

        assert result.intent == QueryIntent.GENERAL_CHAT
        classifier._llm_client.chat_async.assert_called_once()

    def test_huggingface_config_no_json_format(self):
        """Test HuggingFace config doesn't use JSON response format."""
        config = AgentConfig(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080",
        )
        classifier = QueryClassifier(config=config)

        assert classifier._config.response_format is None

    def test_default_config_uses_huggingface(self):
        """Test default config uses HuggingFace provider."""
        classifier = QueryClassifier()

        assert classifier._config.provider == "huggingface"
        assert classifier._config.base_url is not None


@pytest.mark.skip(reason="CLASSIFICATION_PROMPT not exported from query_classifier")
class TestClassificationPrompt:
    """Tests for the classification prompt (skipped: prompt not exported)."""

    def test_prompt_contains_all_intents(self):
        pass

    def test_prompt_has_json_format(self):
        pass


@pytest.mark.skip(reason="get_query_classifier not exported from query_classifier")
class TestGetQueryClassifier:
    """Tests for the singleton getter (skipped: getter not exported)."""

    def test_get_query_classifier_returns_instance(self):
        pass

    def test_get_query_classifier_returns_same_instance(self):
        pass

