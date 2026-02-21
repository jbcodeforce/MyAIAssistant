"""MCP server for MyAIAssistant todos. Exposes create_todo, search_todos, get_todo, update_todo, delete_todo."""

import json
import sys
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .client import (
    get_base_url,
    create_todo as api_create_todo,
    search_todos as api_search_todos,
    get_todo as api_get_todo,
    update_todo as api_update_todo,
    delete_todo as api_delete_todo,
)
from .tools import TOOLS

import httpx

server = Server("myai-todos")


def _body_for_create(args: dict[str, Any]) -> dict[str, Any]:
    """Build POST body from tool arguments; only include provided fields."""
    body: dict[str, Any] = {"title": args["title"]}
    for key in (
        "description", "status", "urgency", "importance",
        "category", "tags", "project_id", "due_date", "source_type", "source_id",
    ):
        if key in args and args[key] is not None:
            body[key] = args[key]
    return body


def _body_for_update(args: dict[str, Any]) -> dict[str, Any]:
    """Build PUT body; exclude todo_id."""
    body: dict[str, Any] = {}
    for key in (
        "title", "description", "status", "urgency", "importance",
        "category", "tags", "project_id", "due_date", "source_type", "source_id",
    ):
        if key in args and args[key] is not None:
            body[key] = args[key]
    return body


def _format_response(status_code: int, text: str) -> str:
    if status_code >= 400:
        try:
            detail = json.loads(text)
            msg = detail.get("detail", text)
            if isinstance(msg, list):
                msg = "; ".join(str(x) for x in msg)
            elif isinstance(msg, dict):
                msg = json.dumps(msg)
            return f"Error {status_code}: {msg}"
        except Exception:
            pass
        return f"Error {status_code}: {text[:500]}"
    return text if text.strip() else f"OK ({status_code})"


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(name=t["name"], description=t["description"], inputSchema=t["inputSchema"])
        for t in TOOLS
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    args = arguments or {}
    base_url = get_base_url()

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            if name == "create_todo":
                body = _body_for_create(args)
                status_code, text = await api_create_todo(client, body)
            elif name == "search_todos":
                status_code, text = await api_search_todos(
                    client,
                    search=args.get("search"),
                    status=args.get("status"),
                    category=args.get("category"),
                    limit=args.get("limit", 100),
                    skip=args.get("skip", 0),
                )
            elif name == "get_todo":
                todo_id = args.get("todo_id")
                if todo_id is None:
                    return [types.TextContent(type="text", text="Error: todo_id is required")]
                status_code, text = await api_get_todo(client, int(todo_id))
            elif name == "update_todo":
                todo_id = args.get("todo_id")
                if todo_id is None:
                    return [types.TextContent(type="text", text="Error: todo_id is required")]
                body = _body_for_update(args)
                status_code, text = await api_update_todo(client, int(todo_id), body)
            elif name == "delete_todo":
                todo_id = args.get("todo_id")
                if todo_id is None:
                    return [types.TextContent(type="text", text="Error: todo_id is required")]
                status_code, text = await api_delete_todo(client, int(todo_id))
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

            return [types.TextContent(type="text", text=_format_response(status_code, text))]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {e!s}")]


async def main() -> None:
    sys.stderr.write("MyAIAssistant todos MCP server starting\n")
    sys.stderr.flush()
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="myai-todos",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
                instructions=(
                    "Use these tools to create, search, get, update, and delete todos in the MyAIAssistant backend. "
                    "Set MYAI_BACKEND_URL to the backend base URL (default http://localhost:8000) if the backend runs elsewhere."
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
