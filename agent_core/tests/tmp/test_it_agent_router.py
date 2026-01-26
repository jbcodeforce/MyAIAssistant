"""Integration tests for agent routing: 
1. Classify query to determine intent
2. Route query to appropriate agent
3. Execute agent and return response
"""

import pytest
import json
from pathlib import Path
from agent_core.agents.agent_factory import AgentFactory
from agent_core.agents.query_classifier import (
    QueryClassifier,
    QueryIntent,
    ClassificationResult,
)
from agent_core.agents.agent_router import AgentRouter
from agent_core.agents.base_agent import BaseAgent, AgentInput, AgentResponse
from .conftest import (
    LOCAL_BASE_URL,
    LOCAL_MODEL,
    requires_ollama,
    requires_model,
)

config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")


@pytest.fixture
def classifier() -> QueryClassifier:
    """Create a QueryClassifier with Ollama config."""
    factory = AgentFactory()
    classifier = factory.create_agent("QueryClassifier")
    return classifier

@pytest.mark.integration
@requires_ollama
@requires_model
class TestAgentRouter:


    @pytest.mark.asyncio
    async def test_classify_code_help_query(self, classifier: QueryClassifier):
        """Test classification of a code help query."""
        query = "How do I implement a REST API endpoint in Python using FastAPI?"
        router = AgentRouter()
        response = await router.route(query)    
        print(json.dumps(response.__dict__, indent=2, default=str))
      

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