"""
Integration tests for the task analysis and recommendations agent (TDD).

Given a taks description as persisted in the database todo table, the agent performs task analysis
and returns recommendations, may be to create a new project, searches knowledge, search the web, 
creates another task or an asset.

For new project, asset or task, it requests human confirmation before creating project/asset/task. Example task
data uses biz-db-like shape (backend Todo).

TaskAgent uses create_task, create_asset and create_project tools. For these tests to avoid
calling a real backend, run agent_service without MYAI_BACKEND_URL (or with
MYAI_USE_MOCK_TASKS=true); the tools then return mock responses.
"""

import json
from pathlib import Path

import pytest
from httpx import AsyncClient
from agent_service.agents.agent_factory import get_or_create_agent_factory
from agent_service.agents.task_agent import Todo

def _fixture_path() -> Path:
    """ One structured persisted task as it could be in the database todo table."""
    return Path(__file__).parent.parent / "fixtures" / "biz_db_task_example.json"


def _load_example_task() -> dict:
    path = _fixture_path()
    with open(path) as f:
        return json.load(f)


def _build_task_message(task: dict) -> str:
    title = task.get("title", "")
    desc = task.get("description", "")
    status = task.get("status", "")
    parts = [f"Title: {title}", f"Status: {status}"]
    if desc:
        parts.append(f"Description: {desc}")
    return "\n".join(parts)


async def _parse_sse_stream(line_stream):
    """Parse Server-Sent Events from an async line iterator. Yields (event_type, data_dict) tuples."""
    event_type = None
    data_buf = []
    async for line in line_stream:
        line = line.rstrip("\r\n") if isinstance(line, str) else line.decode("utf-8").rstrip("\r\n")
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_buf.append(line[5:].strip())
        elif line == "" and (event_type or data_buf):
            data_str = "\n".join(data_buf) if data_buf else "{}"
            try:
                data = json.loads(data_str) if data_str else {}
            except json.JSONDecodeError:
                data = {"raw": data_str}
            yield (event_type or "message", data)
            event_type = None
            data_buf = []


def test_task_agent_runs():
    factory = get_or_create_agent_factory()
    agent = factory.get_or_create_agent("TaskAgent")
    assert agent is not None
    assert agent.name == "TaskAgent"
    #assert agent.tools == ["create_task", "create_asset", "create_project", "websearch"]
    task = _load_example_task()
    assert task is not None
    task_dict = Todo(**task).model_dump()
    agent.print_response(
        input=task_dict,
        stream=True,
    )

@pytest.mark.asyncio
async def  _test_task_analysis_at_highest_api_level(client: AsyncClient):
    """
    Ask TaskAgent to analyze and recommend at the highest API level.
    Assert run completes and response content is non-empty.
    """
    message = "Analyze this task and recommend next steps."
    events = []
    async with client.stream(
        "POST",
        "/agents/TaskAgent/runs",
        data={
            "message": message,
            "stream": "true",
            "session_id": "test_task_analysis_session",
            "user_id": "test_user",
        },
        timeout=90.0,
    ) as response:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.read()}"
        async for event_type, data in _parse_sse_stream(response.aiter_lines()):
            events.append((event_type, data))
    assert len(events) >= 1, "Expected at least one SSE event"
    event_names = [e[0] for e in events]
    assert "RunStarted" in event_names, f"Expected RunStarted in {event_names}"
    last_event = events[-1]
    payload_dict = last_event[1]
    content = payload_dict.get("content")
    print(f"Content: {content}")
    assert content is not None, "Expected non-null content in final event"
    assert isinstance(content, str) and content.strip(), "Expected non-empty content"


@pytest.mark.asyncio
async def _test_task_analysis_continue_with_user_feedback(client: AsyncClient):
    """
    Continue the conversation: first turn asks for analysis and recommendations;
    second turn gives user feedback (confirm action) and asserts the agent responds.
    """
    session_id = "test_task_analysis_feedback_session"
    task = _load_example_task()
    task_block = _build_task_message(task)

    # First turn: analyze and recommend (agent may ask for confirmation)
    turn1_message = (
        "Analyze this task and recommend next steps. "
        "If you recommend creating a project or a new task, ask for human confirmation before doing so. "
        f"Task:\n{task_block}"
    )
    events1 = []
    async with client.stream(
        "POST",
        "/agents/TaskAgent/runs",
        data={
            "message": turn1_message,
            "stream": "true",
            "session_id": session_id,
            "user_id": "test_user",
        },
        timeout=90.0,
    ) as response:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.read()}"
        async for event_type, data in _parse_sse_stream(response.aiter_lines()):
            events1.append((event_type, data))
    assert len(events1) >= 1
    assert "RunStarted" in [e[0] for e in events1]
    content1 = (events1[-1][1].get("content") or "").strip()
    print(f"Content1: {content1}")
    assert content1, "First turn should return non-empty content"

    # Second turn: user feedback confirming the recommendation (continue same session)
    turn2_message = "Yes, go ahead and create the project and the follow-up task you suggested."
    events2 = []
    async with client.stream(
        "POST",
        "/agents/TaskAgent/runs",
        data={
            "message": turn2_message,
            "stream": "true",
            "session_id": session_id,
            "user_id": "test_user",
        },
        timeout=90.0,
    ) as response:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.read()}"
        async for event_type, data in _parse_sse_stream(response.aiter_lines()):
            events2.append((event_type, data))
    assert len(events2) >= 1, "Second turn should emit events"
    assert "RunStarted" in [e[0] for e in events2], "Second turn should emit RunStarted"
    content2 = (events2[-1][1].get("content") or "").strip()
    print(f"Content2: {content2}")
    assert content2, "Second turn (user feedback) should return non-empty content"
    # Agent should acknowledge or reflect the confirmation (e.g. created, done, summary)
    content2_lower = content2.lower()
    assert any(term in content2_lower for term in ("create", "created", "project", "task", "done", "summary", "ok", "completed", "follow-up")), (
        f"Expected second response to acknowledge confirmation or action; got: {content2[:500]}..."
    )
