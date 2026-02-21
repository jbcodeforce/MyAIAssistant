"""Data query agent using Claude Agent SDK and backend-backed tools.

Answers questions about the user's tasks and projects by calling tools
(list_tasks_completed_since, list_tasks_updated_between, get_task_completion_stats,
list_projects, list_tasks_by_project). The provider is injected via context at execute time.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional, Protocol

from agent_core.agents.base_agent import BaseAgent, AgentResponse, AgentInput

logger = logging.getLogger(__name__)

try:
    from claude_agent_sdk import (
        tool,
        create_sdk_mcp_server,
        ClaudeAgentOptions,
        query,
        AssistantMessage,
        TextBlock,
    )
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False


class DataQueryToolProvider(Protocol):
    """Protocol for backend-supplied data query tool implementations."""

    async def list_tasks_completed_since(
        self,
        since: datetime,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return tasks completed on or after the given datetime."""
        ...

    async def list_tasks_updated_between(
        self,
        updated_after: datetime,
        updated_before: datetime,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return tasks updated between the two datetimes."""
        ...

    async def get_task_completion_stats(self, since: datetime) -> list[dict[str, Any]]:
        """Return counts of completed tasks by month from since to now."""
        ...

    async def list_projects(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return list of projects."""
        ...

    async def list_tasks_by_project(
        self,
        project_id: int,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return tasks for a specific project."""
        ...


def _parse_iso_datetime(s: Optional[str]) -> Optional[datetime]:
    """Parse ISO date/datetime string to datetime."""
    if not s or not str(s).strip():
        return None
    s = str(s).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


class DataQueryAgent(BaseAgent):
    """
    Agent that answers questions about the user's tasks and projects using tools.
    Requires data_query_provider in context (injected by backend at request time).
    """

    agent_type = "data_query"

    async def execute(self, input_data: AgentInput) -> AgentResponse:
        """
        Run the data query agent: use tools to fetch tasks/projects/stats,
        then summarize for the user. Provider is read from input_data.context["data_query_provider"].
        """
        if not _SDK_AVAILABLE:
            return AgentResponse(
                message="Data query features require claude-agent-sdk. Install with: uv add claude-agent-sdk",
                agent_type=self.agent_type,
                metadata={"error": "claude-agent-sdk not installed"},
            )
        provider = input_data.context.get("data_query_provider") if input_data.context else None
        if provider is None:
            return AgentResponse(
                message="I cannot query your task data in this context. Data query is only available from the dashboard chat.",
                agent_type=self.agent_type,
                metadata={"error": "data_query_provider not in context"},
            )

        async def list_tasks_completed_since_handler(args: dict) -> dict:
            since_str = args.get("since")
            since = _parse_iso_datetime(since_str)
            if since is None:
                return {"content": [{"type": "text", "text": json.dumps({"error": "Invalid or missing 'since' (ISO datetime required)"})}]}
            limit = int(args.get("limit", 100))
            tasks = await provider.list_tasks_completed_since(since=since, limit=limit)
            return {"content": [{"type": "text", "text": json.dumps({"tasks": tasks, "total": len(tasks)})}]}

        async def list_tasks_updated_between_handler(args: dict) -> dict:
            after = _parse_iso_datetime(args.get("updated_after"))
            before = _parse_iso_datetime(args.get("updated_before"))
            if after is None or before is None:
                return {"content": [{"type": "text", "text": json.dumps({"error": "updated_after and updated_before (ISO datetimes) required"})}]}
            limit = int(args.get("limit", 100))
            tasks = await provider.list_tasks_updated_between(
                updated_after=after, updated_before=before, limit=limit
            )
            return {"content": [{"type": "text", "text": json.dumps({"tasks": tasks, "total": len(tasks)})}]}

        async def get_task_completion_stats_handler(args: dict) -> dict:
            since_str = args.get("since")
            since = _parse_iso_datetime(since_str)
            if since is None:
                return {"content": [{"type": "text", "text": json.dumps({"error": "Invalid or missing 'since' (ISO datetime required)"})}]}
            stats = await provider.get_task_completion_stats(since=since)
            return {"content": [{"type": "text", "text": json.dumps({"by_month": stats})}]}

        async def list_projects_handler(args: dict) -> dict:
            limit = int(args.get("limit", 100))
            projects = await provider.list_projects(limit=limit)
            return {"content": [{"type": "text", "text": json.dumps({"projects": projects})}]}

        async def list_tasks_by_project_handler(args: dict) -> dict:
            try:
                project_id = int(args.get("project_id"))
            except (TypeError, ValueError):
                return {"content": [{"type": "text", "text": json.dumps({"error": "project_id (integer) required"})}]}
            limit = int(args.get("limit", 100))
            tasks = await provider.list_tasks_by_project(project_id=project_id, limit=limit)
            return {"content": [{"type": "text", "text": json.dumps({"tasks": tasks, "total": len(tasks)})}]}

        list_tasks_completed_since_tool = tool(
            "list_tasks_completed_since",
            "List tasks that were completed on or after a given datetime (ISO format). Use for questions like 'tasks I completed last month' or 'completed since 6 months'.",
            {"type": "object", "properties": {"since": {"type": "string", "description": "ISO datetime (e.g. 2024-01-01T00:00:00)"}, "limit": {"type": "integer", "default": 100}}, "required": ["since"]},
        )(list_tasks_completed_since_handler)

        list_tasks_updated_between_tool = tool(
            "list_tasks_updated_between",
            "List tasks that were updated between two datetimes (ISO format). Use for 'tasks I worked on in period X'.",
            {"type": "object", "properties": {"updated_after": {"type": "string"}, "updated_before": {"type": "string"}, "limit": {"type": "integer", "default": 100}}, "required": ["updated_after", "updated_before"]},
        )(list_tasks_updated_between_handler)

        get_task_completion_stats_tool = tool(
            "get_task_completion_stats",
            "Get counts of completed tasks by month from a given datetime. Use for graphs or 'how many tasks completed per month'.",
            {"type": "object", "properties": {"since": {"type": "string", "description": "ISO datetime"}}, "required": ["since"]},
        )(get_task_completion_stats_handler)

        list_projects_tool = tool(
            "list_projects",
            "List all projects (id, name, status, organization_id).",
            {"type": "object", "properties": {"limit": {"type": "integer", "default": 100}}, "required": []},
        )(list_projects_handler)

        list_tasks_by_project_tool = tool(
            "list_tasks_by_project",
            "List tasks belonging to a specific project by project_id.",
            {"type": "object", "properties": {"project_id": {"type": "integer"}, "limit": {"type": "integer", "default": 100}}, "required": ["project_id"]},
        )(list_tasks_by_project_handler)

        server = create_sdk_mcp_server(
            name="data-query-db",
            version="1.0.0",
            tools=[
                list_tasks_completed_since_tool,
                list_tasks_updated_between_tool,
                get_task_completion_stats_tool,
                list_projects_tool,
                list_tasks_by_project_tool,
            ],
        )

        system_prompt = (self._config.sys_prompt or self._load_system_prompt()) if self._config else self._load_system_prompt()
        model = getattr(self._config, "model", "claude-sonnet-4-5") or "claude-sonnet-4-5"
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"db": server},
            allowed_tools=[
                "mcp__db__list_tasks_completed_since",
                "mcp__db__list_tasks_updated_between",
                "mcp__db__get_task_completion_stats",
                "mcp__db__list_projects",
                "mcp__db__list_tasks_by_project",
            ],
            permission_mode="bypassPermissions",
            max_turns=5,
            model=model,
        )

        prompt = input_data.query
        last_text = ""
        chart_data = None
        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            last_text = block.text
        except Exception as e:
            logger.exception("DataQueryAgent SDK query failed: %s", e)
            return AgentResponse(
                message=f"I encountered an error while querying your data: {e}",
                agent_type=self.agent_type,
                metadata={"error": str(e)},
            )

        # Optionally parse chart_data from last_text for frontend (e.g. by_month table)
        metadata = {}
        if chart_data is not None:
            metadata["chart_data"] = chart_data
        return AgentResponse(
            message=last_text or "I could not produce an answer.",
            agent_type=self.agent_type,
            metadata=metadata,
        )
