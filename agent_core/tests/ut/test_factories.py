"""
Tests for the AgentFactory class.

These tests drive the implementation of a config-driven agent factory
that loads agent definitions from YAML config files.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from agent_core.agents.agent_factory import AgentFactory, AgentConfig
from agent_core.agents.base_agent import BaseAgent, AgentInput, AgentResponse
from agent_core.providers.llm_provider_factory import LLMProviderFactory
from agent_core.providers.llm_provider_base import LLMProvider
from agent_core.agents.query_classifier import QueryClassifier


config_dir = str(Path(__file__).parent.parent.parent /"agent_core" / "agents" / "config")

class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_agent_config_from_yaml(self, tmp_path):
        """Test loading AgentConfig from a YAML file."""
        # Create a test agent.yaml
        agent_dir = tmp_path / "TestAgent"
        agent_dir.mkdir()
        yaml_content = """
            name: TestAgent
            description: A test agent
            provider: huggingface
            model: gpt-4o-mini
            temperature: 0.5
            max_tokens: 1000
        """
        (agent_dir / "agent.yaml").write_text(yaml_content)
        
        config = AgentConfig.from_yaml(agent_dir / "agent.yaml")
        
        assert config.name == "TestAgent"
        assert config.description == "A test agent"
        assert config.agent_class == "agent_core.agents.base_agent.BaseAgent"
        # provider is always "huggingface", not stored in config
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000

    def test_agent_config_with_class(self, tmp_path):
        """Test AgentConfig with a fully qualified class name."""
        agent_dir = tmp_path / "QueryClassifier"
        agent_dir.mkdir()
        yaml_content = """
name: QueryClassifier
description: Classifies queries
class: agent_core.agents.query_classifier.QueryClassifier
provider: huggingface
model: gpt-4o-mini
temperature: 0.0
max_tokens: 500
"""
        (agent_dir / "agent.yaml").write_text(yaml_content)
        
        config = AgentConfig.from_yaml(agent_dir / "agent.yaml")
        
        assert config.name == "QueryClassifier"
        assert config.agent_class == "agent_core.agents.query_classifier.QueryClassifier"
        assert config.temperature == 0.0

    def test_agent_config_validate_success(self):
        """Test AgentConfig validation succeeds for valid config."""
        config = AgentConfig(
            name="TestAgent",
            provider="huggingface",
            model="gpt-4o-mini",
            base_url="http://localhost:8080",  # Local server, no api_key needed
            temperature=0.7
        )
        
        # Should not raise
        config.validate()

    def test_agent_config_validate_invalid_temperature(self):
        """Test AgentConfig validation fails for invalid temperature."""
        config = AgentConfig(
            name="TestAgent",
            provider="huggingface",
            model="gpt-4o-mini",
            base_url="http://localhost:8080",
            temperature=3.0  # Invalid: > 2.0
        )
        
        with pytest.raises(ValueError, match="Temperature must be between"):
            config.validate()


class TestProviderFactory:
    """Tests for the ProviderFactory class."""

    def test_create_provider(self):
        """Test creating a provider."""
        provider = LLMProviderFactory.create_provider("huggingface")
        assert provider is not None

    def test_create_provider_invalid(self):
        """Test creating an invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            LLMProviderFactory.create_provider("invalid")

class TestAgentFactory:
    """Tests for the AgentFactory class."""

    @pytest.fixture
    def factory(self):
        """Create an agent factory for testing."""
        return AgentFactory(config_dir=config_dir)

    def test_factory_discovers_agents(self, factory):
        """Test that factory discovers agent configs from directory."""
        agent_names = factory.list_agents()
        
        assert "QueryClassifier" in agent_names
        assert "GeneralAgent" in agent_names
        assert len(agent_names) >= 2

    def test_factory_loads_agent_yaml(self, factory):
        """Test factory loads agent.yaml correctly."""
        config = factory.get_config("QueryClassifier")
        
        assert config is not None
        assert config.name == "QueryClassifier"
        assert config.description is not None
        # provider is always "huggingface", not stored in config
        assert config.model == "mistral:7b-instruct"
        assert config.temperature == 0.0
        assert config.max_tokens == 500


    def test_factory_returns_none_for_unknown_agent(self, factory):
        """Test factory returns None for unknown agent names."""
        config = factory.get_config("NonExistentAgent")        
        assert config is None

    def test_create_agent_returns_correct_type(self, factory):
        agent = factory.create_agent("GeneralAgent")
        assert agent is not None
        assert isinstance(agent, BaseAgent)
        assert agent._config.model == "gpt-oss:20b"
        assert agent._config.temperature == 0.7
        assert agent._config.max_tokens >= 2000
        assert agent._system_prompt is not None

   
    def test_create_query_classifier_agent_returns_correct_type(self, factory):
        agent = factory.create_agent("QueryClassifier")
        assert agent is not None
        assert isinstance(agent, QueryClassifier)
        assert agent._config.model == "mistral:7b-instruct"
        assert agent._config.temperature == 0.0
        assert agent._config.max_tokens >= 500
        assert agent._system_prompt is not None


class TestAgentInput:
    """Tests for AgentInput base class."""

    def test_agent_input_defaults(self):
        """Test AgentInput with default values."""
        input_data = AgentInput(query="test query")
        
        assert input_data.query == "test query"
        assert input_data.conversation_history == []
        assert input_data.context == {}

    def test_agent_input_with_all_fields(self):
        """Test AgentInput with all fields specified."""
        history = [{"role": "user", "content": "hello"}]
        context = {"task_id": "123"}
        
        input_data = AgentInput(
            query="test query",
            conversation_history=history,
            context=context
        )
        
        assert input_data.query == "test query"
        assert input_data.conversation_history == history
        assert input_data.context == context


class TestAgentFactoryDynamicImport:
    """Tests for dynamic class import functionality."""

    def test_import_class_success(self):
        """Test successful dynamic import of a class."""
        factory = AgentFactory()
        
        # Test importing BaseAgent directly
        cls = factory._import_class("agent_core.agents.base_agent.BaseAgent")
        
        from agent_core.agents.base_agent import BaseAgent
        assert cls is BaseAgent

    def test_import_class_invalid_format(self):
        """Test import with invalid format raises ImportError."""
        factory = AgentFactory(config_dir=config_dir)
        
        with pytest.raises(ImportError, match="Invalid fully qualified class name"):
            factory._import_class("InvalidClassName")

    def test_import_class_module_not_found(self):
        """Test import with non-existent module raises ImportError."""
        factory = AgentFactory()
        
        with pytest.raises(ImportError):
            factory._import_class("non_existent_module.SomeClass")

    def test_import_class_class_not_found(self):
        """Test import with non-existent class raises AttributeError."""
        factory = AgentFactory()
        
        with pytest.raises(AttributeError):
            factory._import_class("agent_core.agents.base_agent.NonExistentClass")

    def test_resolve_agent_class_not_base_agent(self):
        """Test that non-BaseAgent class raises ValueError."""
        factory = AgentFactory()
        
        with pytest.raises(ValueError, match="not a subclass of BaseAgent"):
            # Try to use a class that's not a BaseAgent
            factory._resolve_agent_class("agent_core.agents.agent_factory.AgentConfig")

    def test_resolve_agent_class_none_returns_default(self):
        """Test that None class returns BaseAgent."""
        factory = AgentFactory()
        
        cls = factory._resolve_agent_class(None)
        
        from agent_core.agents.base_agent import BaseAgent
        assert cls is BaseAgent


