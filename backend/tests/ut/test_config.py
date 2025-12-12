"""Unit tests for config.py - validates YAML configuration loading and overrides."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import yaml


class TestYamlConfigOverrides:
    """Test that CONFIG_FILE environment variable properly overrides settings."""

    def test_default_database_url(self):
        """Test that default database_url is loaded from app/config.yaml."""
        # Import fresh to avoid cached settings
        from importlib import reload
        import app.core.config as config_module
        
        # Clear any CONFIG_FILE env var
        with patch.dict(os.environ, {}, clear=False):
            if "CONFIG_FILE" in os.environ:
                del os.environ["CONFIG_FILE"]
            
            # Reload to get fresh settings
            reload(config_module)
            settings = config_module.Settings()
            
            # Default from app/config.yaml
            assert settings.database_url == "sqlite+aiosqlite:///./myaiassistant.db"

    def test_yaml_config_overrides_database_url(self):
        """Test that CONFIG_FILE yaml properly overrides database_url."""
        custom_db_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        
        # Create a temporary YAML config file with custom database_url
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            yaml.dump({"database_url": custom_db_url}, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            # Set CONFIG_FILE environment variable
            with patch.dict(os.environ, {"CONFIG_FILE": tmp_file_path}):
                from importlib import reload
                import app.core.config as config_module
                
                # Force reload of the module to pick up new env var
                reload(config_module)
                
                # Create new Settings instance
                settings = config_module.Settings()
                
                assert settings.database_url == custom_db_url
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)

    def test_yaml_config_partial_override(self):
        """Test that CONFIG_FILE only overrides specified values, keeping defaults."""
        custom_db_url = "sqlite+aiosqlite:///./custom_override.db"
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            # Only override database_url, leave other settings to defaults
            yaml.dump({"database_url": custom_db_url}, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            with patch.dict(os.environ, {"CONFIG_FILE": tmp_file_path}):
                from importlib import reload
                import app.core.config as config_module
                
                reload(config_module)
                settings = config_module.Settings()
                
                # database_url should be overridden
                assert settings.database_url == custom_db_url
                
                # Other settings should retain defaults from app/config.yaml
                assert settings.app_name == "MyAIAssistant Backend"
                assert settings.llm_provider == "ollama"
                assert settings.chroma_collection_name == "knowledge_base"
        finally:
            os.unlink(tmp_file_path)

    def test_env_var_takes_precedence_over_yaml(self):
        """Test that environment variables have higher priority than YAML config."""
        yaml_db_url = "postgresql+asyncpg://yaml:yaml@localhost/yamldb"
        env_db_url = "postgresql+asyncpg://env:env@localhost/envdb"
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            yaml.dump({"database_url": yaml_db_url}, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            # Set both CONFIG_FILE and DATABASE_URL env vars
            with patch.dict(
                os.environ,
                {"CONFIG_FILE": tmp_file_path, "DATABASE_URL": env_db_url}
            ):
                from importlib import reload
                import app.core.config as config_module
                
                reload(config_module)
                settings = config_module.Settings()
                
                # Environment variable should take precedence over YAML
                assert settings.database_url == env_db_url
        finally:
            os.unlink(tmp_file_path)

    def test_nonexistent_config_file_uses_defaults(self):
        """Test that nonexistent CONFIG_FILE falls back to defaults."""
        with patch.dict(
            os.environ, {"CONFIG_FILE": "/nonexistent/path/config.yaml"}
        ):
            from importlib import reload
            import app.core.config as config_module
            
            reload(config_module)
            settings = config_module.Settings()
            
            # Should use default from app/config.yaml
            assert settings.database_url == "sqlite+aiosqlite:///./myaiassistant.db"

    def test_yaml_config_overrides_multiple_fields(self):
        """Test that multiple fields can be overridden via YAML."""
        custom_config = {
            "database_url": "postgresql+asyncpg://multi:test@localhost/multidb",
            "llm_provider": "openai",
            "llm_model": "gpt-4",
            "llm_temperature": 0.7,
        }
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            yaml.dump(custom_config, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            with patch.dict(os.environ, {"CONFIG_FILE": tmp_file_path}):
                from importlib import reload
                import app.core.config as config_module
                
                reload(config_module)
                settings = config_module.Settings()
                
                assert settings.database_url == custom_config["database_url"]
                assert settings.llm_provider == custom_config["llm_provider"]
                assert settings.llm_model == custom_config["llm_model"]
                assert settings.llm_temperature == custom_config["llm_temperature"]
        finally:
            os.unlink(tmp_file_path)


class TestYamlConfigSettingsSource:
    """Test the YamlConfigSettingsSource class directly."""

    def test_load_yaml_file_returns_empty_for_missing_file(self):
        """Test that _load_yaml_file returns empty dict for missing files."""
        from app.core.config import YamlConfigSettingsSource, Settings
        
        source = YamlConfigSettingsSource(Settings)
        result = source._load_yaml_file(Path("/nonexistent/file.yaml"))
        
        assert result == {}

    def test_load_yaml_file_returns_empty_for_empty_file(self):
        """Test that _load_yaml_file returns empty dict for empty YAML files."""
        from app.core.config import YamlConfigSettingsSource, Settings
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            tmp_file.write("")  # Empty file
            tmp_file_path = tmp_file.name
        
        try:
            source = YamlConfigSettingsSource(Settings)
            result = source._load_yaml_file(Path(tmp_file_path))
            
            assert result == {}
        finally:
            os.unlink(tmp_file_path)

    def test_load_yaml_file_parses_valid_yaml(self):
        """Test that _load_yaml_file correctly parses valid YAML."""
        from app.core.config import YamlConfigSettingsSource, Settings
        
        test_data = {"database_url": "test://db", "app_name": "Test App"}
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            yaml.dump(test_data, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            source = YamlConfigSettingsSource(Settings)
            result = source._load_yaml_file(Path(tmp_file_path))
            
            assert result == test_data
        finally:
            os.unlink(tmp_file_path)


class TestSettingsDefaults:
    """Test Settings class default values."""

    def test_settings_has_expected_defaults(self):
        """Test that Settings class has expected default values."""
        from app.core.config import Settings
        
        # Create settings with no external config
        with patch.dict(os.environ, {}, clear=False):
            if "CONFIG_FILE" in os.environ:
                del os.environ["CONFIG_FILE"]
            if "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            
            from importlib import reload
            import app.core.config as config_module
            reload(config_module)
            
            settings = config_module.Settings()
            
            # Verify key defaults
            assert settings.app_name == "MyAIAssistant Backend"
            assert settings.app_version == "0.1.0"
            assert settings.database_url == "sqlite+aiosqlite:///./myaiassistant.db"
            assert settings.chroma_persist_directory == "./data/chroma"
            assert settings.llm_provider == "ollama"
            assert settings.llm_max_tokens == 2048
            assert settings.llm_temperature == 0.1

    def test_cors_origins_is_list(self):
        """Test that cors_origins is properly loaded as a list."""
        from importlib import reload
        import app.core.config as config_module
        
        with patch.dict(os.environ, {}, clear=False):
            if "CONFIG_FILE" in os.environ:
                del os.environ["CONFIG_FILE"]
            
            reload(config_module)
            settings = config_module.Settings()
            
            assert isinstance(settings.cors_origins, list)
            assert "http://localhost:5173" in settings.cors_origins
            assert "http://localhost:3000" in settings.cors_origins


class TestSingletonPattern:
    """Test the get_settings() singleton pattern."""

    def test_get_settings_returns_same_instance(self):
        """Test that get_settings() returns the same instance on repeated calls."""
        from importlib import reload
        import app.core.config as config_module
        
        reload(config_module)
        config_module.reset_settings()  # Clear any existing singleton
        
        settings1 = config_module.get_settings()
        settings2 = config_module.get_settings()
        
        assert settings1 is settings2

    def test_reset_settings_clears_singleton(self):
        """Test that reset_settings() clears the singleton instance."""
        from importlib import reload
        import app.core.config as config_module
        
        reload(config_module)
        config_module.reset_settings()
        
        settings1 = config_module.get_settings()
        config_module.reset_settings()
        settings2 = config_module.get_settings()
        
        # After reset, we should get a new instance
        assert settings1 is not settings2

    def test_get_settings_respects_config_file(self):
        """Test that get_settings() singleton respects CONFIG_FILE."""
        custom_db_url = "postgresql+asyncpg://singleton:test@localhost/singletondb"
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as tmp_file:
            yaml.dump({"database_url": custom_db_url}, tmp_file)
            tmp_file_path = tmp_file.name
        
        try:
            with patch.dict(os.environ, {"CONFIG_FILE": tmp_file_path}):
                from importlib import reload
                import app.core.config as config_module
                
                reload(config_module)
                config_module.reset_settings()
                
                settings = config_module.get_settings()
                
                assert settings.database_url == custom_db_url
        finally:
            os.unlink(tmp_file_path)

    def test_get_config_info_returns_resolved_paths(self):
        """Test that get_config_info() returns properly resolved paths."""
        from importlib import reload
        import app.core.config as config_module
        
        reload(config_module)
        config_module.reset_settings()
        
        info = config_module.get_config_info()
        
        assert "config_file" in info
        assert "database_url" in info
        assert "resolved_database_path" in info
        assert "chroma_persist_directory" in info
        assert "resolved_chroma_path" in info
        assert "chroma_collection_name" in info
        
        # Resolved paths should be absolute
        assert Path(info["resolved_database_path"]).is_absolute()
        assert Path(info["resolved_chroma_path"]).is_absolute()

