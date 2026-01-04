"""Tests for type definitions."""

import pytest
from datetime import datetime

from agent_core.types import Message, LLMResponse, LLMError


class TestMessage:
    """Tests for Message dataclass."""
    
    def test_create_user_message(self):
        """Test creating a user message."""
        msg = Message(role="user", content="Hello!")
        assert msg.role == "user"
        assert msg.content == "Hello!"
    
    def test_create_system_message(self):
        """Test creating a system message."""
        msg = Message(role="system", content="You are helpful.")
        assert msg.role == "system"
    
    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = Message(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
    
    def test_to_dict(self):
        """Test converting message to dictionary."""
        msg = Message(role="user", content="Test")
        d = msg.to_dict()
        
        assert d == {"role": "user", "content": "Test"}


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""
    
    def test_create_response(self):
        """Test creating a response."""
        response = LLMResponse(
            content="Hello!",
            model="gpt-4",
            provider="openai"
        )
        
        assert response.content == "Hello!"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.usage is None
        assert isinstance(response.created_at, datetime)
    
    def test_response_with_usage(self):
        """Test response with token usage."""
        response = LLMResponse(
            content="Response",
            model="gpt-4",
            provider="openai",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        )
        
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30
    
    def test_response_without_usage(self):
        """Test token properties when usage is None."""
        response = LLMResponse(
            content="Response",
            model="gpt-4",
            provider="openai"
        )
        
        assert response.prompt_tokens == 0
        assert response.completion_tokens == 0
        assert response.total_tokens == 0
    
    def test_response_with_finish_reason(self):
        """Test response with finish reason."""
        response = LLMResponse(
            content="Done",
            model="gpt-4",
            provider="openai",
            finish_reason="stop"
        )
        
        assert response.finish_reason == "stop"


class TestLLMError:
    """Tests for LLMError exception."""
    
    def test_create_error(self):
        """Test creating an error."""
        error = LLMError(
            message="Rate limit exceeded",
            provider="openai"
        )
        
        assert error.message == "Rate limit exceeded"
        assert error.provider == "openai"
        assert error.status_code is None
    
    def test_error_with_status_code(self):
        """Test error with status code."""
        error = LLMError(
            message="Unauthorized",
            provider="openai",
            status_code=401
        )
        
        assert error.status_code == 401
    
    def test_error_str_with_status(self):
        """Test error string representation with status code."""
        error = LLMError(
            message="Rate limit",
            provider="openai",
            status_code=429
        )
        
        assert "[openai] 429: Rate limit" == str(error)
    
    def test_error_str_without_status(self):
        """Test error string representation without status code."""
        error = LLMError(
            message="Connection failed",
            provider="ollama"
        )
        
        assert "[ollama] Connection failed" == str(error)
    
    def test_error_is_exception(self):
        """Test that LLMError is an Exception."""
        error = LLMError(message="Test", provider="test")
        assert isinstance(error, Exception)

