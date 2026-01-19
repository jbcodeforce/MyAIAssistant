"""Integration tests for agent router with real Ollama calls.

These tests require a running Ollama instance with the specified model.
Run with: pytest tests/it/ -v -m integration
"""

import os
import pytest
import httpx


from agent_core.agents.factory import AgentConfig, AgentFactory
from agent_core.agents.query_classifier import (
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
)
from agent_core.agents.agent_router import AgentRouter, get_agent_router
from agent_core.agents.base_agent import BaseAgent, AgentInput, AgentResponse


# Default model for integration tests - can be overridden via env var
OLLAMA_MODEL = os.getenv("OLLAMA_TEST_MODEL", "mistral-small")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def is_ollama_available() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


def is_model_available(model: str) -> bool:
    """Check if the specified model is available in Ollama."""
    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
        if response.status_code != 200:
            return False
        data = response.json()
        models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
        return model in models or any(model in m for m in models)
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


# Skip markers for integration tests
requires_ollama = pytest.mark.skipif(
    not is_ollama_available(),
    reason="Ollama is not running or not accessible"
)


@pytest.fixture
def classifier() -> QueryClassifier:
    """Create a QueryClassifier with Ollama config."""
    factory = AgentFactory()
    classifier = factory.create_agent("QueryClassifier")
    return classifier

@pytest.mark.integration
@requires_ollama
class TestQueryClassifierOllama:

    @pytest.mark.asyncio
    async def test_classify_knowledge_search_query(self, classifier: BaseAgent):
        """Test classification of a knowledge search query."""
        query = "What does our documentation say about OAuth authentication?"
        
        result = await classifier.execute(AgentInput(query=query))
        
        assert isinstance(result, AgentResponse)
        assert result.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert result.confidence >= 0.5
        assert len(result.reasoning) > 0
        assert isinstance(result.entities, dict)

    @pytest.mark.asyncio
    async def test_classify_code_help_query(self, classifier: QueryClassifier):
        """Test classification of a code help query."""
        query = "How do I implement a REST API endpoint in Python using FastAPI?"
        
        result = await classifier.classify(query)
        
        assert isinstance(result, ClassificationResult)
        assert result.intent == QueryIntent.CODE_HELP
        assert result.confidence >= 0.5
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_classify_task_planning_query(self, classifier: QueryClassifier):
        """Test classification of a task planning query."""
        query = "Help me plan the steps to migrate our database from MySQL to PostgreSQL"
        
        result = await classifier.classify(query)
        
        assert isinstance(result, ClassificationResult)
        assert result.intent == QueryIntent.TASK_PLANNING
        assert result.confidence >= 0.5
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_classify_general_chat_query(self, classifier: QueryClassifier):
        """Test classification of a general chat query."""
        query = "Hello, how are you doing today?"
        
        result = await classifier.classify(query)
        
        assert isinstance(result, ClassificationResult)
        assert result.intent == QueryIntent.GENERAL_CHAT
        assert result.confidence >= 0.5
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_classify_task_status_query(self, classifier: QueryClassifier):
        """Test classification of a task status query."""
        query = "What is the current status of my pending tasks?"
        
        result = await classifier.classify(query)
        
        assert isinstance(result, ClassificationResult)
        assert result.intent == QueryIntent.TASK_STATUS
        assert result.confidence >= 0.5
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_classify_with_conversation_context(self, classifier: QueryClassifier):
        """Test classification with conversation history context."""
        query = "Tell me more about that"
        conversation_context = [
            {"role": "user", "content": "What does the API documentation say about rate limits?"},
            {"role": "assistant", "content": "The API has a rate limit of 100 requests per minute."},
        ]
        
        result = await classifier.classify(query, conversation_context)
        
        assert isinstance(result, ClassificationResult)
        # With context about documentation, should lean towards knowledge search
        assert result.intent in [QueryIntent.KNOWLEDGE_SEARCH, QueryIntent.GENERAL_CHAT]
        assert result.confidence >= 0.3

    @pytest.mark.asyncio
    async def test_classification_returns_entities(self, classifier: QueryClassifier):
        """Test that classification extracts entities from the query."""
        query = "Search our knowledge base for Python FastAPI authentication examples"
        
        result = await classifier.classify(query)
        
        assert isinstance(result, ClassificationResult)
        assert isinstance(result.entities, dict)
        # The entities should contain some extracted information
        # Note: exact entity extraction depends on the model

    def test_classify_sync_knowledge_search(self, classifier: QueryClassifier):
        """Test synchronous classification of a knowledge search query."""
        query = "Find information about our deployment process in the docs"
        
        result = classifier.classify_sync(query)
        
        assert isinstance(result, ClassificationResult)
        assert result.intent == QueryIntent.KNOWLEDGE_SEARCH
        assert result.confidence >= 0.5
        assert len(result.reasoning) > 0

    def test_classify_sync_code_help(self, classifier: QueryClassifier):
        """Test synchronous classification of a code help query."""
        query = "Write a Python function to sort a list of dictionaries by date"
        
        result = classifier.classify_sync(query)
        
        assert isinstance(result, ClassificationResult)
        assert result.intent == QueryIntent.CODE_HELP
        assert result.confidence >= 0.5


@pytest.mark.integration
@requires_ollama
class TestClassificationAccuracy:
    """Tests for assessing classification accuracy with various query types."""

    KNOWLEDGE_QUERIES = [
        "What does our documentation say about authentication?",
        "Search the knowledge base for deployment guides",
        "Find information about the API rate limits",
        "Look up our security policies",
        "What do we have documented about error handling?",
    ]

    CODE_QUERIES = [
        "How do I implement JWT authentication in FastAPI?",
        "Write a Python script to parse JSON files",
        "Debug this SQL query that's returning wrong results",
        "Create a React component for a dropdown menu",
        "Explain how async/await works in JavaScript",
    ]

    TASK_QUERIES = [
        "Help me plan the database migration project",
        "Create a checklist for releasing the new feature",
        "Break down the steps to refactor the auth module",
        "What tasks do I need to complete before deployment?",
        "Organize my work for the sprint",
    ]

    GENERAL_QUERIES = [
        "Hello, how are you?",
        "Thanks for your help!",
        "Good morning",
        "What time is it?",
        "Tell me a joke",
    ]

    @pytest.mark.asyncio
    async def test_knowledge_search_accuracy(self, classifier: QueryClassifier):
        """Test classification accuracy for knowledge search queries."""
        correct = 0
        for query in self.KNOWLEDGE_QUERIES:
            result = await classifier.classify(query)
            if result.intent == QueryIntent.KNOWLEDGE_SEARCH:
                correct += 1
        
        accuracy = correct / len(self.KNOWLEDGE_QUERIES)
        # Expect at least 60% accuracy for knowledge queries
        assert accuracy >= 0.6, f"Knowledge search accuracy too low: {accuracy:.0%}"

    @pytest.mark.asyncio
    async def test_code_help_accuracy(self, classifier: QueryClassifier):
        """Test classification accuracy for code help queries."""
        correct = 0
        for query in self.CODE_QUERIES:
            result = await classifier.classify(query)
            if result.intent == QueryIntent.CODE_HELP:
                correct += 1
        
        accuracy = correct / len(self.CODE_QUERIES)
        # Expect at least 60% accuracy for code queries
        assert accuracy >= 0.6, f"Code help accuracy too low: {accuracy:.0%}"

    @pytest.mark.asyncio
    async def test_task_planning_accuracy(self, classifier: QueryClassifier):
        """Test classification accuracy for task planning queries."""
        correct = 0
        for query in self.TASK_QUERIES:
            result = await classifier.classify(query)
            if result.intent in [QueryIntent.TASK_PLANNING, QueryIntent.TASK_STATUS]:
                correct += 1
        
        accuracy = correct / len(self.TASK_QUERIES)
        # Expect at least 60% accuracy for task queries
        assert accuracy >= 0.6, f"Task planning accuracy too low: {accuracy:.0%}"

    @pytest.mark.asyncio
    async def test_general_chat_accuracy(self, classifier: QueryClassifier):
        """Test classification accuracy for general chat queries."""
        correct = 0
        for query in self.GENERAL_QUERIES:
            result = await classifier.classify(query)
            if result.intent == QueryIntent.GENERAL_CHAT:
                correct += 1
        
        accuracy = correct / len(self.GENERAL_QUERIES)
        # Expect at least 60% accuracy for general chat
        assert accuracy >= 0.6, f"General chat accuracy too low: {accuracy:.0%}"

    
    async def test_research_accuracy(self, classifier: QueryClassifier):
        """Test classification accuracy for research queries."""
        correct = 0
        agent_router = get_agent_router()   
        for query in self.RESEARCH_QUERIES:
            result = await agent_router.route(query)
            if result.intent == QueryIntent.RESEARCH:
                correct += 1
        
        accuracy = correct / len(self.RESEARCH_QUERIES)
        # Expect at least 60% accuracy for research queries
        assert accuracy >= 0.6, f"Research accuracy too low: {accuracy:.0%}"