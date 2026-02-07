"""Tests for the default HuggingFace InferenceClient adapter."""

import pytest
from unittest.mock import MagicMock, patch

from agent_core.agents.agent_config import AgentConfig
from agent_core.types import LLMError
from agent_core.agents._llm_default import (
    DefaultHFAdapter,
    _get_hf_token,
    _is_local_server,
    _parse_response,
    _raise_llm_error,
)


class TestDefaultHFAdapter:
    """Tests for DefaultHFAdapter (default HuggingFace InferenceClient path)."""

    @pytest.fixture
    def adapter(self):
        return DefaultHFAdapter()

    @pytest.fixture
    def config_remote(self):
        return AgentConfig(
            name="TestAgent",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            api_key="hf_test_token",
            base_url=None,
        )

    @pytest.fixture
    def config_local(self):
        return AgentConfig(
            name="TestAgent",
            model="llama3",
            base_url="http://localhost:8080",
        )

    @pytest.fixture
    def messages(self):
        return [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
        ]

    def test_adapter_has_chat_async_and_chat_sync(self, adapter):
        assert hasattr(adapter, "chat_async")
        assert hasattr(adapter, "chat_sync")
        assert callable(adapter.chat_async)
        assert callable(adapter.chat_sync)


class TestDefaultHFAdapterHelpers:
    """Tests for module-level helpers used by DefaultHFAdapter."""

    def test_get_hf_token_from_config(self):
        config = AgentConfig(
            name="Test",
            model="test",
            api_key="hf_config_token",
            base_url=None,
        )
        assert _get_hf_token(config) == "hf_config_token"

    def test_get_hf_token_from_env(self):
        config = AgentConfig(name="Test", model="test", base_url="http://localhost:8080")
        with patch.dict("os.environ", {"HF_TOKEN": "hf_env_token"}):
            assert _get_hf_token(config) == "hf_env_token"

    def test_is_local_server_remote(self):
        config = AgentConfig(
            name="Test",
            model="meta-llama/Model",
            base_url=None,
        )
        assert _is_local_server(config) is False

    def test_is_local_server_local(self):
        config = AgentConfig(
            name="Test",
            model="llama3",
            base_url="http://localhost:8080",
        )
        assert _is_local_server(config) is True

    def test_parse_response(self):
        config = AgentConfig(
            name="Test",
            model="meta-llama/Meta-Llama-3-8B-Instruct",
            base_url=None,
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello there!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "meta-llama/Meta-Llama-3-8B-Instruct"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.model_dump = MagicMock(return_value={})

        response = _parse_response(mock_response, config)

        assert response.content == "Hello there!"
        assert response.model == "meta-llama/Meta-Llama-3-8B-Instruct"
        assert response.provider == "huggingface"
        assert response.finish_reason == "stop"
        assert response.total_tokens == 15

    def test_parse_response_no_usage(self):
        config = AgentConfig(name="Test", model="llama3", base_url=None)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "llama3"
        mock_response.usage = None
        mock_response.model_dump = MagicMock(return_value={})

        response = _parse_response(mock_response, config)

        assert response.content == "Hello!"
        assert response.usage is None

    def test_raise_llm_error(self):
        error = Exception("Connection refused")
        with pytest.raises(LLMError) as exc_info:
            _raise_llm_error(error)
        assert "Connection refused" in str(exc_info.value)
        assert exc_info.value.provider == "huggingface"
