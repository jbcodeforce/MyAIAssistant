# Claude Agent SDK (Python) – Reference

Longer examples for custom tools and multi-turn client usage.

## Multi-tool MCP server with ClaudeSDKClient

Define multiple tools, create an SDK MCP server, and use `ClaudeSDKClient` for interactive queries.

```python
import asyncio
from typing import Any
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    tool,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add_numbers(args: dict[str, Any]) -> dict[str, Any]:
    result = args["a"] + args["b"]
    return {"content": [{"type": "text", "text": f"{args['a']} + {args['b']} = {result}"}]}

@tool("divide", "Divide two numbers", {"a": float, "b": float})
async def divide_numbers(args: dict[str, Any]) -> dict[str, Any]:
    if args["b"] == 0:
        return {"content": [{"type": "text", "text": "Error: Division by zero"}], "is_error": True}
    result = args["a"] / args["b"]
    return {"content": [{"type": "text", "text": f"{args['a']} / {args['b']} = {result}"}]}

async def main():
    calculator = create_sdk_mcp_server(
        name="calculator",
        version="1.0.0",
        tools=[add_numbers, divide_numbers],
    )

    options = ClaudeAgentOptions(
        mcp_servers={"calc": calculator},
        allowed_tools=["mcp__calc__add", "mcp__calc__divide"],
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Calculate 15 + 27, then divide the result by 6")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
                    elif isinstance(block, ToolUseBlock):
                        print(f"Using tool: {block.name} with input: {block.input}")

asyncio.run(main())
```

## Tool with JSON Schema (enums, complex args)

For enums or complex validation, use a JSON Schema dict as the third argument to `@tool`.

```python
import os
import json
import aiohttp
from typing import Any
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool(
    "api_request",
    "Make authenticated API requests to external services",
    {
        "type": "object",
        "properties": {
            "service": {"type": "string", "enum": ["stripe", "github", "openai", "slack"]},
            "endpoint": {"type": "string"},
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
            "body": {"type": "object"},
            "query": {"type": "object"},
        },
        "required": ["service", "endpoint", "method"],
    },
)
async def api_request(args: dict[str, Any]) -> dict[str, Any]:
    config = {
        "stripe": {"base_url": "https://api.stripe.com/v1", "key": os.environ.get("STRIPE_KEY", "")},
        "github": {"base_url": "https://api.github.com", "key": os.environ.get("GITHUB_TOKEN", "")},
        "openai": {"base_url": "https://api.openai.com/v1", "key": os.environ.get("OPENAI_KEY", "")},
        "slack": {"base_url": "https://slack.com/api", "key": os.environ.get("SLACK_TOKEN", "")},
    }

    service_config = config[args["service"]]
    url = f"{service_config['base_url']}{args['endpoint']}"

    if args.get("query"):
        params = "&".join([f"{k}={v}" for k, v in args["query"].items()])
        url += f"?{params}"

    headers = {
        "Authorization": f"Bearer {service_config['key']}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.request(
            args["method"], url, headers=headers, json=args.get("body")
        ) as response:
            data = await response.json()
            return {
                "content": [{"type": "text", "text": json.dumps(data, indent=2)}],
            }

api_gateway_server = create_sdk_mcp_server(
    name="api-gateway",
    version="1.0.0",
    tools=[api_request],
)
```

## Bug-fixing agent with query()

One-shot agent that reviews and fixes a file using built-in tools.

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    async for message in query(
        prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],
            permission_mode="acceptEdits",
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")

asyncio.run(main())
```
