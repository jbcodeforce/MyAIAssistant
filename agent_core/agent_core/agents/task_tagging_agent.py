"""Task tagging agent using Claude Agent SDK and backend-backed tools.

Classifies tasks with tags using get_available_tags, task_list, and update_task
tools. Tools are executed in backend context via an injected tool_provider.
"""

import json
import logging
import re
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


class TaskTaggingToolProvider(Protocol):
    """Protocol for backend-supplied tool implementations."""

    async def get_available_tags(self) -> list[str]:
        """Return list of existing tag strings used in the system."""
        ...

    async def task_list(
        self,
        skip: int = 0,
        limit: int = 100,
        todo_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Return list of tasks (id, title, description, tags, ...). If todo_id is set, return that task only."""
        ...

    async def update_task(self, todo_id: int, tags: list[str]) -> dict[str, Any]:
        """Update the given task's tags. Return success info."""
        ...


class TaskTaggingAgent(BaseAgent):
    """
    Agent that classifies tasks with tags using Claude Agent SDK and
    backend-backed tools (get_available_tags, task_list, update_task).

    Requires a tool_provider when used for tagging; tools run in backend context.
    """

    agent_type = "task_tagging"

    def __init__(self, tool_provider: Optional[TaskTaggingToolProvider] = None, **kwargs):
        super().__init__(**kwargs)
        self._tool_provider = tool_provider

    async def execute(self, input_data: AgentInput) -> AgentResponse:
        """
        Run the tagging agent: use tools to get tags and tasks, then classify
        and update the task. Returns AgentResponse with metadata["tags"].
        """
        if not _SDK_AVAILABLE:
            return AgentResponse(
                message="TaskTaggingAgent requires claude-agent-sdk. Install with: uv add claude-agent-sdk",
                agent_type=self.agent_type,
                metadata={"tags": [], "error": "claude-agent-sdk not installed"},
            )
        if self._tool_provider is None:
            return AgentResponse(
                message="TaskTaggingAgent requires a tool_provider when used for tagging.",
                agent_type=self.agent_type,
                metadata={"tags": [], "error": "tool_provider required"},
            )

        provider = self._tool_provider

        async def get_available_tags_handler(args: dict) -> dict:
            tags = await provider.get_available_tags()
            return {"content": [{"type": "text", "text": json.dumps({"tags": tags})}]}

        async def task_list_handler(args: dict) -> dict:
            skip = int(args.get("skip", 0))
            limit = int(args.get("limit", 100))
            todo_id = args.get("todo_id")
            if todo_id is not None:
                todo_id = int(todo_id)
            tasks = await provider.task_list(skip=skip, limit=limit, todo_id=todo_id)
            return {"content": [{"type": "text", "text": json.dumps({"tasks": tasks})}]}

        async def update_task_handler(args: dict) -> dict:
            todo_id = int(args["todo_id"])
            tags = list(args.get("tags", []))
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            result = await provider.update_task(todo_id=todo_id, tags=tags)
            return {"content": [{"type": "text", "text": json.dumps(result)}]}

        get_available_tags_tool = tool(
            "get_available_tags",
            "Return the list of available tag strings used in the system. Call this first to know which tags you can assign.",
            {},
        )(get_available_tags_handler)

        task_list_tool = tool(
            "task_list",
            "List tasks. Returns tasks with id, title, description, tags. Use todo_id to fetch a single task.",
            {
                "type": "object",
                "properties": {
                    "skip": {"type": "integer", "default": 0},
                    "limit": {"type": "integer", "default": 100},
                    "todo_id": {"type": "integer"},
                },
                "required": [],
            },
        )(task_list_handler)

        update_task_tool = tool(
            "update_task",
            "Update a task's tags. Pass todo_id and a list of tag strings.",
            {"todo_id": int, "tags": list},
        )(update_task_handler)

        server = create_sdk_mcp_server(
            name="task-tagging-db",
            version="1.0.0",
            tools=[get_available_tags_tool, task_list_tool, update_task_tool],
        )

        system_prompt = self.build_system_prompt(input_data.context or {})
        model = getattr(self._config, "model", "claude-sonnet-4-5") or "claude-sonnet-4-5"
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"db": server},
            allowed_tools=[
                "mcp__db__get_available_tags",
                "mcp__db__task_list",
                "mcp__db__update_task",
            ],
            permission_mode="bypassPermissions",
            max_turns=5,
            model=model,
        )

        prompt = input_data.query
        context = input_data.context or {}
        if context.get("todo_id") is not None:
            prompt = f"{prompt}\n\nTask ID to tag: {context['todo_id']}."
        if context.get("task_title"):
            prompt = f"{prompt}\n\nTask title: {context['task_title']}."
        if context.get("task_description"):
            prompt = f"{prompt}\n\nTask description: {context['task_description']}."

        last_text = ""
        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            last_text = block.text
        except Exception as e:
            logger.exception("TaskTaggingAgent SDK query failed: %s", e)
            return AgentResponse(
                message=str(e),
                agent_type=self.agent_type,
                metadata={"tags": [], "error": str(e)},
            )

        tags = self._parse_tags_from_response(last_text)
        return AgentResponse(
            message=last_text or "No response.",
            agent_type=self.agent_type,
            metadata={"tags": tags},
        )

    def _parse_tags_from_response(self, text: str) -> list[str]:
        """Extract list of tags from assistant response (e.g. JSON block or inline)."""
        if not text or not text.strip():
            return []
        try:
            json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            if json_match:
                data = json.loads(json_match.group(1).strip())
                if isinstance(data.get("tags"), list):
                    return [str(t) for t in data["tags"]]
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end > start:
                data = json.loads(text[start : end + 1])
                if isinstance(data.get("tags"), list):
                    return [str(t) for t in data["tags"]]
        except (json.JSONDecodeError, TypeError):
            pass
        return []
