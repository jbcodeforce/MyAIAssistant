"""
Tests for the AgentFactory class.

These tests drive the implementation of a config-driven agent factory
that loads agent definitions from YAML config files.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from agent_core.agents.agent_factory import AgentFactory, get_agent_factory
from agent_core.agents.base_agent import BaseAgent, AgentInput
from agent_core.agents.agent_config import AgentConfig, LOCAL_MODEL, LOCAL_BASE_URL
from agent_core.agents.query_classifier import QueryClassifier
from agent_core.agents.agent_router import AgentRouter

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
            model: gpt-4o-mini
            temperature: 0.5
            max_tokens: 1000
        """
        (agent_dir / "agent.yaml").write_text(yaml_content)
        
        config = AgentConfig.from_yaml(agent_dir / "agent.yaml")
        
        assert config.name == "TestAgent"
        assert config.description == "A test agent"
        assert config.agent_class == "agent_core.agents.base_agent.BaseAgent"
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
            model="gpt-4o-mini",
            base_url=LOCAL_BASE_URL,  # Local server, no api_key needed
            temperature=0.7
        )
        
        # Should not raise
        config.validate()

    def test_agent_config_validate_invalid_temperature(self):
        """Test AgentConfig validation fails for invalid temperature."""
        config = AgentConfig(
            name="TestAgent",
            model="gpt-4o-mini",
            base_url=LOCAL_BASE_URL,
            temperature=3.0  # Invalid: > 2.0
        )
        
        with pytest.raises(ValueError, match="Temperature must be between"):
            config.validate()

    def test_load_base_agents(self):
        """Test loading base agents from the config folder."""
        _config_dir = Path(__file__).parent.parent.parent / "agent_core" / "agents" / "config"
        config = AgentConfig.from_yaml(_config_dir /  "GeneralAgent" / "agent.yaml")
        assert config is not None
        assert config.name == "GeneralAgent"
        assert config.temperature == 0.4
        assert config.max_tokens == 4096

    def test_agent_config_llm_url_from_yaml(self, tmp_path):
        """Test that llm_url in YAML is mapped to base_url."""
        agent_dir = tmp_path / "CustomLLMAgent"
        agent_dir.mkdir()
        yaml_content = """
name: CustomLLMAgent
description: Agent with custom LLM endpoint
model: some-model
llm_url: http://custom:1337/v1
"""
        (agent_dir / "agent.yaml").write_text(yaml_content)
        config = AgentConfig.from_yaml(agent_dir / "agent.yaml")
        assert config.base_url == "http://custom:1337/v1"

    def test_agent_config_llm_url_overrides_base_url(self, tmp_path):
        """Test that llm_url takes precedence over base_url when both are set."""
        agent_dir = tmp_path / "OverrideAgent"
        agent_dir.mkdir()
        yaml_content = """
name: OverrideAgent
model: test-model
base_url: http://default:1234/v1
llm_url: http://custom:1337/v1
"""
        (agent_dir / "agent.yaml").write_text(yaml_content)
        config = AgentConfig.from_yaml(agent_dir / "agent.yaml")
        assert config.base_url == "http://custom:1337/v1"


class TestAgentFactory:
    """Tests for the AgentFactory class."""

    @pytest.fixture
    def factory(self):
        """Create an agent factory for testing."""
        return get_agent_factory(config_dir=config_dir)

    def test_factory_singleton(self):
        """Test loading default agents from the config folder."""
        factory = get_agent_factory(config_dir=config_dir)
        assert factory is not None
        assert factory._configs is not None
        assert len(factory._configs) >= 2
        factory = get_agent_factory()
        assert factory is not None

    def test_factory_singleton_no_config_dir(self):
        """Test loading default agents from the config folder."""
        factory = get_agent_factory()
        assert factory is not None
        assert factory._configs is not None
        assert len(factory._configs) >= 2
        print(factory._configs)

    def test_factory_discovers_agents(self, factory):
        """Test that factory discovers agent configs from directory."""
        agent_names = factory.list_agents()
        
        assert "QueryClassifier" in agent_names
        assert "GeneralAgent" in agent_names
        assert len(agent_names) >= 2

    def test_factory_loads_agent_yaml(self, factory):
        """Test factory loads agent.yaml correctly."""
        config = factory._configs.get("QueryClassifier")
        
        assert config is not None
        assert config.name == "QueryClassifier"
        assert config.description is not None
        # provider is always "huggingface", not stored in config
        assert config.model == LOCAL_MODEL
        assert config.temperature == 0.1
        assert config.max_tokens == 2048


    def test_factory_returns_none_for_unknown_agent(self, factory):
        """Test factory returns None for unknown agent names."""
        config = factory._configs.get("NonExistentAgent")        
        assert config is None

    def test_create_agent_returns_correct_type(self, factory):
        agent = factory.create_agent("GeneralAgent")
        assert agent is not None
        assert isinstance(agent, BaseAgent)
        assert agent._config.model == LOCAL_MODEL
        assert agent._config.temperature == 0.4
        assert agent._config.max_tokens >= 4096
        assert agent._config.sys_prompt is not None

   
    def test_create_query_classifier_agent_returns_correct_type(self, factory):
        agent = factory.create_agent("QueryClassifier")
        assert agent is not None
        assert isinstance(agent, QueryClassifier)
        assert agent._config.model == LOCAL_MODEL
        assert agent._config.temperature == 0.1
        assert agent._config.max_tokens >= 2048
        assert agent._config.sys_prompt is not None

    def test_factory_loads_from_custom_config_dir(self, tmp_path):
        """Test that factory loads agents from a custom config_dir."""
        # Create a custom agent configuration directory
        custom_agent_dir = tmp_path / "CustomAgent"
        custom_agent_dir.mkdir()
        
        # Create agent.yaml
        yaml_content = """
name: CustomAgent
description: A custom agent for testing
class: agent_core.agents.base_agent.BaseAgent
model: gpt-4o-mini
temperature: 0.8
max_tokens: 3000
"""
        (custom_agent_dir / "agent.yaml").write_text(yaml_content)
        
        # Create prompt.md
        prompt_content = "You are a custom test agent. Provide helpful responses."
        (custom_agent_dir / "prompt.md").write_text(prompt_content)
        
        # Create factory with custom config_dir and defaults enabled
        factory = AgentFactory(load_defaults=True, config_dir=str(tmp_path))
        
        # Verify custom agent is loaded
        agent_names = factory.list_agents()
        assert "CustomAgent" in agent_names
        
        # Verify custom agent config
        config = factory._configs.get("CustomAgent")
        assert config is not None
        assert config.name == "CustomAgent"
        assert config.description == "A custom agent for testing"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.8
        assert config.max_tokens == 3000
        assert config.agent_dir is not None
        assert str(config.agent_dir) == str(custom_agent_dir)
        
        # Verify default agents are also loaded
        assert "GeneralAgent" in agent_names or "QueryClassifier" in agent_names
        
        # Verify we can create the custom agent
        agent = factory.create_agent("CustomAgent")
        assert agent is not None
        assert isinstance(agent, BaseAgent)
        assert agent._config.name == "CustomAgent"
        assert agent._config.model == "gpt-4o-mini"
        assert agent._config.temperature == 0.8
        # Verify prompt was loaded from filesystem
        assert "custom test agent" in agent._config.sys_prompt.lower()

    def test_factory_custom_config_dir_overrides_defaults(self, tmp_path):
        """Test that custom config_dir agents override default agents with same name."""
        # Create a custom GeneralAgent that overrides the default
        custom_agent_dir = tmp_path / "GeneralAgent"
        custom_agent_dir.mkdir()
        
        yaml_content = """
name: GeneralAgent
description: Custom GeneralAgent that overrides default
model: custom-model
temperature: 0.9
max_tokens: 5000
"""
        (custom_agent_dir / "agent.yaml").write_text(yaml_content)
        
        # Create factory with defaults and custom config_dir
        factory = AgentFactory(load_defaults=True, config_dir=str(tmp_path))
        
        # Verify custom GeneralAgent overrides default
        config = factory._configs.get("GeneralAgent")
        assert config is not None
        assert config.name == "GeneralAgent"
        assert config.description == "Custom GeneralAgent that overrides default"
        assert config.model == "custom-model"
        assert config.temperature == 0.9
        assert config.max_tokens == 5000
        # Verify it's from filesystem, not resources
        assert config.agent_dir is not None
        assert str(config.agent_dir) == str(custom_agent_dir)
        assert str(config.agent_dir) != "__resource__"

    def test_factory_custom_config_dir_only(self, tmp_path):
        """Test factory with custom config_dir and defaults disabled."""
        # Create a custom agent
        custom_agent_dir = tmp_path / "CustomOnlyAgent"
        custom_agent_dir.mkdir()
        
        yaml_content = """
name: CustomOnlyAgent
description: Agent only in custom config
model: test-model
temperature: 0.5
"""
        (custom_agent_dir / "agent.yaml").write_text(yaml_content)
        
        # Create factory with defaults disabled
        factory = AgentFactory(load_defaults=False, config_dir=str(tmp_path))
        
        # Verify only custom agent is loaded
        agent_names = factory.list_agents()
        assert "CustomOnlyAgent" in agent_names
        assert len(agent_names) == 1
        
        # Verify default agents are not loaded
        assert "GeneralAgent" not in agent_names
        assert "QueryClassifier" not in agent_names


    def test_factory_create_persona_agent(self):
        """Test creating a PersonaAgent."""
        factory = get_agent_factory()
        agent = factory.create_agent("PersonaAgent")
        assert agent is not None
        assert isinstance(agent, BaseAgent)
        assert agent._config.model == LOCAL_MODEL
        assert agent._config.temperature == 0.5
        assert agent._config.max_tokens == 2048
        assert agent._config.sys_prompt is not None
        assert len(agent._config.sys_prompt) > 10
       
    def test_factory_create_router_agent(self):
        """Test creating a RouterAgent."""
        factory = get_agent_factory()
        agent = factory.create_agent("AgentRouter")
        assert agent is not None
        assert isinstance(agent, AgentRouter)
        assert agent._config.model == LOCAL_MODEL
        assert agent._config.temperature == 0.2
        assert agent._config.max_tokens == 4096
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


