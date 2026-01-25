"""Unit tests for query classification agent."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from agent_core.agents.query_classifier import (
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
    get_query_classifier,
    CLASSIFICATION_PROMPT
)

from agent_core.agents.base_agent import AgentInput
from agent_core.types import LLMResponse


class TestQueryIntent:
    """Tests for QueryIntent enum."""
    
    def test_intent_from_string(self):
        """Test creating intent from string value."""
        intent = QueryIntent("knowledge_search")
        assert intent == QueryIntent.KNOWLEDGE_SEARCH
    
    def test_intent_invalid_string_raises(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError):
            QueryIntent("invalid_intent")


class TestQueryClassifier:
    """Tests for QueryClassifier class."""
    
    @pytest.fixture
    def classifier(self):
        """Create a query classifier for testing."""
        return QueryClassifier(
            provider="huggingface",
            model="mistral:7b-instruct",
            api_key="test-key"
        )
    
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

    @pytest.mark.asyncio
    async def test_classify_knowledge_search(self, classifier, mock_llm_response_knowledge):
        """Test classifying a knowledge search query."""
        mock_llm_response = LLMResponse(
            content=mock_llm_response_knowledge,
            model=classifier.model,
            provider="huggingface"
        )
        
        with patch.object(classifier._llm_client, 'chat_async', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_llm_response
            
            result = await classifier.execute(
                AgentInput(
                    query="What does our documentation say about ai assistant?",
                    conversation_history=[],
                    context={}
                )
            )
            
            assert result.metadata['intent'] == QueryIntent.KNOWLEDGE_SEARCH.value
            assert result.metadata['confidence'] == 0.92
            assert "authentication" in result.metadata['entities'].get("topic", "")
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_task_planning(self, classifier, mock_llm_response_task):
        """Test classifying a task planning query."""
        with patch.object(classifier, '_call_llm_for_classification', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_llm_response_task
            
            result = await classifier.classify(
                "Help me break down the database migration into steps"
            )
            
            assert result.intent == QueryIntent.TASK_PLANNING
            assert result.confidence == 0.88
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_code_help(self, classifier, mock_llm_response_code):
        """Test classifying a code help query."""
        with patch.object(classifier, '_call_llm_for_classification', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_llm_response_code
            
            result = await classifier.classify(
                "How do I implement JWT authentication in FastAPI?"
            )
            
            assert result.intent == QueryIntent.CODE_HELP
            assert result.confidence == 0.95
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_general_chat(self, classifier, mock_llm_response_general):
        """Test classifying a general chat query."""
        with patch.object(classifier, '_call_llm_for_classification', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_llm_response_general
            
            result = await classifier.classify("Hello, how are you today?")
            
            assert result.intent == QueryIntent.GENERAL_CHAT
            assert result.confidence == 0.75
            mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_with_conversation_context(self, classifier, mock_llm_response_knowledge):
        """Test classification with conversation context."""
        with patch.object(classifier, '_call_llm_for_classification', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_llm_response_knowledge
            
            context = [
                {"role": "user", "content": "I'm looking for security docs"},
                {"role": "assistant", "content": "What specifically about security?"}
            ]
            
            result = await classifier.classify(
                "The OAuth implementation",
                conversation_context=context
            )
            
            assert result.intent == QueryIntent.KNOWLEDGE_SEARCH
            # Verify the prompt includes context
            call_args = mock_call.call_args[0][0]
            assert "Previous conversation context" in call_args

    @pytest.mark.asyncio
    async def test_classify_handles_llm_error(self, classifier):
        """Test that classification handles LLM errors gracefully."""
        with patch.object(classifier, '_call_llm_for_classification', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API Error")
            
            result = await classifier.classify("Any query")
            
            # Should fall back to general chat
            assert result.intent == QueryIntent.GENERAL_CHAT
            assert result.confidence == 0.5
            assert "Classification failed" in result.reasoning

    @pytest.mark.asyncio
    async def test_classify_handles_invalid_json(self, classifier):
        """Test handling of invalid JSON response from LLM."""
        with patch.object(classifier, '_call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "This is not valid JSON"
            
            result = await classifier.classify("Test query")
            
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
            "entities": {}
        }
        markdown_response = f"```json\n{json.dumps(json_content)}\n```"
        
        with patch.object(classifier, '_call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = markdown_response
            
            result = await classifier.classify("Help me plan this task")
            
            assert result.intent == QueryIntent.TASK_PLANNING
            assert result.confidence == 0.85

    @pytest.mark.asyncio
    async def test_classify_handles_unknown_intent(self, classifier):
        """Test handling of unknown intent value from LLM."""
        response = json.dumps({
            "intent": "unknown_intent_type",
            "confidence": 0.9,
            "reasoning": "Unknown type",
            "entities": {}
        })
        
        with patch.object(classifier, '_call_llm', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = response
            
            result = await classifier.classify("Test query")
            
            # Should default to general chat
            assert result.intent == QueryIntent.GENERAL_CHAT


class TestQueryClassifierLLMClient:
    """Tests for QueryClassifier LLM client integration."""
    
    def test_classifier_has_llm_client(self):
        """Test that classifier creates LLMClient."""
        from agent_core import LLMClient
        
        classifier = QueryClassifier(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        assert hasattr(classifier, '_llm_client')
        assert isinstance(classifier._llm_client, LLMClient)
    
    def test_classifier_has_agent_config(self):
        """Test that classifier creates AgentConfig."""
        from agent_core import AgentConfig
        
        classifier = QueryClassifier(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        assert hasattr(classifier, '_config')
        assert isinstance(classifier._config, AgentConfig)
        assert classifier._config.provider == "openai"
        assert classifier._config.temperature == 0.1  # Low for classification
    
    @pytest.mark.asyncio
    async def test_call_llm_uses_client(self):
        """Test that _call_llm_for_classification uses LLMClient."""
        from agent_core import LLMResponse
        
        classifier = QueryClassifier(
            provider="openai",
            model="gpt-4",
            api_key="test-key"
        )
        
        mock_response = LLMResponse(
            content='{"intent": "general_chat", "confidence": 0.8, "reasoning": "test", "entities": {}}',
            model="gpt-4",
            provider="openai"
        )
        
        classifier._llm_client.chat_async = AsyncMock(return_value=mock_response)
        
        result = await classifier._call_llm_for_classification("Test prompt")
        
        assert result == mock_response.content
        classifier._llm_client.chat_async.assert_called_once()
    
    def test_huggingface_config_no_json_format(self):
        """Test HuggingFace config doesn't use JSON response format."""
        classifier = QueryClassifier(
            provider="huggingface",
            model="llama3",
            base_url="http://localhost:8080"
        )
        
        # HuggingFace provider doesn't use response_format
        assert classifier._config.response_format is None
    
    def test_default_config_uses_huggingface(self):
        """Test default config uses HuggingFace provider."""
        classifier = QueryClassifier()
        
        assert classifier._config.provider == "huggingface"
        # base_url is None by default, provider handles default URL
        assert classifier._config.base_url is None


class TestClassificationPrompt:
    """Tests for the classification prompt."""
    
    def test_prompt_contains_all_intents(self):
        """Test that prompt includes all intent types."""
        assert "knowledge_search" in CLASSIFICATION_PROMPT
        assert "task_planning" in CLASSIFICATION_PROMPT
        assert "task_status" in CLASSIFICATION_PROMPT
        assert "general_chat" in CLASSIFICATION_PROMPT
        assert "code_help" in CLASSIFICATION_PROMPT
        assert "unclear" in CLASSIFICATION_PROMPT
    
    def test_prompt_has_json_format(self):
        """Test that prompt requests JSON output."""
        assert "JSON" in CLASSIFICATION_PROMPT or "json" in CLASSIFICATION_PROMPT
        assert "intent" in CLASSIFICATION_PROMPT
        assert "confidence" in CLASSIFICATION_PROMPT
        assert "reasoning" in CLASSIFICATION_PROMPT
        assert "entities" in CLASSIFICATION_PROMPT


class TestGetQueryClassifier:
    """Tests for the singleton getter."""
    
    def test_get_query_classifier_returns_instance(self):
        """Test that get_query_classifier returns a QueryClassifier."""
        # Reset the global instance for testing
        import agent_core.agents.query_classifier as qc_module
        qc_module._classifier = None
        
        classifier = get_query_classifier()
        
        assert isinstance(classifier, QueryClassifier)
    
    def test_get_query_classifier_returns_same_instance(self):
        """Test singleton behavior."""
        import agent_core.agents.query_classifier as qc_module
        qc_module._classifier = None
        
        classifier1 = get_query_classifier()
        classifier2 = get_query_classifier()
        
        assert classifier1 is classifier2

