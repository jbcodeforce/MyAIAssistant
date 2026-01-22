"""
Tests for the AgentFactory class.

These tests drive the implementation of a config-driven agent factory
that loads agent definitions from YAML config files.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from agent_core.agents.factory import AgentFactory, AgentConfig
from agent_core.agents.base_agent import BaseAgent, AgentInput


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
        assert config.agent_class is None  # Uses BaseAgent when class is omitted
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

    def test_agent_config_validate_invalid_provider(self):
        """Test AgentConfig validation fails for invalid provider."""
        with pytest.raises(ValueError, match="HF_TOKEN is required"):
            config = AgentConfig(
                name="TestAgent",
                model="gpt-4"
            )
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


class TestAgentFactory:
    """Tests for the AgentFactory class."""

    @pytest.fixture
    def config_dir(self, tmp_path):
        """Create a temporary config directory with test agents."""
        # Create QueryClassifier config with fully qualified class name
        qc_dir = tmp_path / "QueryClassifier"
        qc_dir.mkdir()
        (qc_dir / "agent.yaml").write_text("""
name: QueryClassifier
description: Classifies user queries for routing
class: agent_core.agents.query_classifier.QueryClassifier
provider: huggingface
model: gpt-4o-mini
temperature: 0.0
max_tokens: 500
""")
        (qc_dir / "prompt.md").write_text("""You are a query classifier.
Classify the user's query into categories.

User Query: {query}
""")
        
        # Create GeneralAgent config without class (uses BaseAgent)
        ga_dir = tmp_path / "GeneralAgent"
        ga_dir.mkdir()
        (ga_dir / "agent.yaml").write_text("""
name: GeneralAgent
description: General purpose assistant
# class field omitted - uses BaseAgent
provider: huggingface
model: gpt-4o-mini
temperature: 0.7
max_tokens: 2000
""")
        (ga_dir / "prompt.md").write_text("""You are a helpful assistant.
Be clear and concise in your responses.
""")
        
        return tmp_path

    @pytest.fixture
    def factory(self, config_dir):
        """Create an agent factory for testing."""
        return AgentFactory(config_dir=config_dir)

    def test_factory_discovers_agents(self, factory):
        """Test that factory discovers agent configs from directory."""
        agent_names = factory.list_agents()
        
        assert "QueryClassifier" in agent_names
        assert "GeneralAgent" in agent_names
        assert len(agent_names) == 2

    def test_factory_loads_agent_yaml(self, factory):
        """Test factory loads agent.yaml correctly."""
        config = factory.get_config("QueryClassifier")
        
        assert config is not None
        assert config.name == "QueryClassifier"
        assert config.description == "Classifies user queries for routing"
        # provider is always "huggingface", not stored in config
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.0
        assert config.max_tokens == 500


    def test_factory_returns_none_for_unknown_agent(self, factory):
        """Test factory returns None for unknown agent names."""
        config = factory.get_config("NonExistentAgent")        
        assert config is None

    def test_create_agent_returns_correct_type(self, factory):
        """Test creating an agent returns correct instance."""
        mock_instance = MagicMock(spec=BaseAgent)
        mock_instance.agent_type = "general"
        MockAgent = MagicMock(return_value=mock_instance)
        
        with patch.object(factory, '_resolve_agent_class', return_value=MockAgent):
            agent = factory.create_agent("GeneralAgent")
            
            assert agent is not None
            MockAgent.assert_called_once()

    def test_create_agent_injects_config(self, factory):
        """Test that created agent receives config values."""
        mock_instance = MagicMock(spec=BaseAgent)
        MockAgent = MagicMock(return_value=mock_instance)
        
        with patch.object(factory, '_resolve_agent_class', return_value=MockAgent):
            factory.create_agent("GeneralAgent")
            
            # Verify config was passed to constructor
            call_kwargs = MockAgent.call_args.kwargs
            # provider is always "huggingface", not passed to agent constructor
            assert call_kwargs.get('model') == 'gpt-4o-mini'
            assert call_kwargs.get('temperature') == 0.7
            assert call_kwargs.get('max_tokens') == 2000

    def test_create_agent_injects_prompt(self, factory):
        """Test that created agent receives system prompt."""
        mock_instance = MagicMock(spec=BaseAgent)
        MockAgent = MagicMock(return_value=mock_instance)
        
        with patch.object(factory, '_resolve_agent_class', return_value=MockAgent):
            factory.create_agent("GeneralAgent")
            
            call_kwargs = MockAgent.call_args.kwargs
            assert 'system_prompt' in call_kwargs
            assert "helpful assistant" in call_kwargs['system_prompt'].lower()

    def test_create_agent_raises_for_unknown(self, factory):
        """Test creating unknown agent raises ValueError."""
        with pytest.raises(ValueError, match="Unknown agent"):
            factory.create_agent("NonExistentAgent")

    def test_factory_uses_default_config_dir(self):
        """Test factory uses default config directory when not specified."""
        factory = AgentFactory()
        
        # Default should be the config folder in the agents module
        assert factory.config_dir.name == "config"
        assert factory.config_dir.parent.name == "agents"


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
        factory = AgentFactory()
        
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
            factory._resolve_agent_class("agent_core.agents.factory.AgentConfig")

    def test_resolve_agent_class_none_returns_default(self):
        """Test that None class returns BaseAgent."""
        factory = AgentFactory()
        
        cls = factory._resolve_agent_class(None)
        
        from agent_core.agents.base_agent import BaseAgent
        assert cls is BaseAgent


class TestAgentFactoryWithRealAgents:
    """Integration tests using actual config directory."""

    @pytest.fixture
    def real_factory(self):
        """Create factory pointing to real config directory."""
        return AgentFactory()

    def test_loads_query_classifier_config(self, real_factory):
        """Test loading actual QueryClassifier config."""
        if "QueryClassifier" not in real_factory.list_agents():
            pytest.skip("QueryClassifier config not found")
        
        config = real_factory.get_config("QueryClassifier")
        
        assert config is not None
        assert config.name == "QueryClassifier"
        # provider is always "huggingface", not stored in config
        assert config.model is not None
        # Verify fully qualified class name
        assert "agent_core.agents" in config.agent_class


    def test_create_real_agent(self, real_factory):
        """Test creating an agent using real config with dynamic import."""
        if "GeneralAgent" not in real_factory.list_agents():
            pytest.skip("GeneralAgent config not found")
        
        agent = real_factory.create_agent("GeneralAgent")
        
        from agent_core.agents.base_agent import BaseAgent
        assert isinstance(agent, BaseAgent)
        assert agent._system_prompt is not None
