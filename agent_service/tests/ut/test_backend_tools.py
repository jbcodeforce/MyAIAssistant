"""Unit tests for create_task and create_project tools (mock mode)."""

import os

import pytest
from agent_service.tools.backend_tools import create_task, create_project


@pytest.fixture(autouse=True)
def use_mock_tools(monkeypatch):
    """Force mock mode so tests do not call the real backend."""
    monkeypatch.delenv("MYAI_BACKEND_URL", raising=False)
    monkeypatch.setenv("MYAI_USE_MOCK_TASKS", "true")


@pytest.mark.asyncio
async def test_create_task_mock_returns_id_and_title():
    result = await create_task(title="Test task", description="A test")
    assert result["id"] == 9001
    assert result["title"] == "Test task"
    assert "message" in result
    assert "Mock" in result["message"]


@pytest.mark.asyncio
async def test_create_task_mock_accepts_optional_fields():
    result = await create_task(
        title="Urgent item",
        status="Open",
        urgency="Urgent",
        importance="Important",
        project_id=1,
    )
    assert result["title"] == "Urgent item"
    assert result["id"] == 9001


@pytest.mark.asyncio
async def test_create_project_mock_returns_id_and_name():
    result = await create_project(name="Test project", description="A test project")
    assert result["id"] == 8001
    assert result["name"] == "Test project"
    assert "message" in result
    assert "Mock" in result["message"]


@pytest.mark.asyncio
async def test_create_project_mock_accepts_optional_fields():
    result = await create_project(
        name="Q1 Migration",
        status="Draft",
        organization_id=1,
        tasks="- Step one\n- Step two",
    )
    assert result["name"] == "Q1 Migration"
    assert result["id"] == 8001
