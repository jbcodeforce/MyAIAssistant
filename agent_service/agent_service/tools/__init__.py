"""Tools for agents: create_task and create_project (backend REST or mock for tests)."""

from agent_service.tools.backend_tools import (
    create_task,
    create_project,
    TASK_PROJECT_TOOL_REGISTRY,
)

__all__ = ["create_task", "create_project", "TASK_PROJECT_TOOL_REGISTRY"]
