---
name: claude-agent-sdk
description: Guides development of agents using the Claude Agent SDK for Python: setup, custom tools with @tool and MCP, permission modes, and query vs ClaudeSDKClient. Use when the user is building a Python agent with Claude Agent SDK, adding tools, configuring MCP servers, or debugging agent loops.
---

# Claude Agent SDK (Python)

## Quick reference

**Installation**

```bash
pip install claude-agent-sdk
# or
uv add claude-agent-sdk
```

Set `ANTHROPIC_API_KEY` (env or config).

**Two entry points**

- **`query(prompt, options)`** – Stateless, one-shot. The SDK runs the agent loop and executes tools. Use for simple tasks.
- **`ClaudeSDKClient(options)`** – Stateful, multi-turn. Supports custom tools and hooks. Use `client.query(...)` and `client.receive_response()`.

## Core concepts

**Agent loop** – The SDK runs the loop (Claude -> tool use -> results -> Claude). Do not implement a manual tool loop when using `query()` or `ClaudeSDKClient`.

**Built-in tools** – Read, Edit, Write, Glob, Grep, Bash. Restrict via `allowed_tools` in `ClaudeAgentOptions`.

**Permission modes** (`permission_mode`)

| Value | Behavior |
|-------|----------|
| `default` | Normal permission prompts |
| `acceptEdits` | Auto-approve file edits (Edit, Write, and certain fs operations) |
| `plan` | Planning only; no execution |
| `bypassPermissions` | Skip permission prompts (use with care; e.g. read-only agents) |

## Custom tools

**Define** – Use `@tool("name", "description", args_schema)` on an `async def`. `args_schema` can be a dict of `{name: type}` or a JSON Schema dict for enums or complex types.

**Return shape** – Return a dict: `{"content": [{"type": "text", "text": "..."}]}`. Optionally add `"is_error": True` for failures.

**Register** – Call `create_sdk_mcp_server(name, version, tools=[...])`, then pass the result to `ClaudeAgentOptions(mcp_servers={"key": server}, allowed_tools=["mcp__key__tool_name", ...])`.

**Naming** – Allowed tool IDs are `mcp__<server_key>__<tool_name>`.

**Minimal example**

```python
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
)

@tool("greet", "Greet a user", {"name": str})
async def greet_user(args):
    return {
        "content": [{"type": "text", "text": f"Hello, {args['name']}!"}]
    }

server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[greet_user],
)

options = ClaudeAgentOptions(
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__greet"],
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Greet Alice")
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(block.text)
```

## Configuration (ClaudeAgentOptions)

Common options: `system_prompt`, `allowed_tools`, `permission_mode`, `max_turns`, `cwd`, `model`.

**Read-only agent** – Restrict to safe tools and bypass prompts:

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Glob", "Grep"],
    permission_mode="bypassPermissions",
)
```

**Code-edit agent** – Allow file edits with auto-approval:

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Edit", "Glob"],
    permission_mode="acceptEdits",
)
```

**Simple query with options**

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

options = ClaudeAgentOptions(
    system_prompt="You are a helpful assistant.",
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="acceptEdits",
    max_turns=5,
    cwd="/path/to/project",
    model="claude-sonnet-4-5",
)

async for message in query(prompt="Create a hello.py with a greeting function", options=options):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
```

## Message types (streaming)

When consuming the async iterator from `query()` or `client.receive_response()`:

- **Messages**: `AssistantMessage`, `ResultMessage`
- **Content blocks**: `TextBlock`, `ToolUseBlock`

Use `isinstance(message, AssistantMessage)` and `isinstance(block, TextBlock)` (or `ToolUseBlock`) to handle each item.

```python
async for message in query(prompt="...", options=options):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
            elif isinstance(block, ToolUseBlock):
                print(f"Tool: {block.name} input: {block.input}")
    elif isinstance(message, ResultMessage):
        print(f"Done: {message.subtype}")
```

## Patterns and anti-patterns

**Do**

- Use `query()` for simple one-shot tasks; use `ClaudeSDKClient` when you need multi-turn or custom tools/hooks.
- Keep tool handlers async and return the documented content shape; set `is_error` for failures.
- Use JSON Schema for tool args when you have enums or nested objects.

**Avoid**

- Implementing a manual tool loop when using the Agent SDK (the SDK already runs it).
- Using `bypassPermissions` unless necessary (e.g. read-only or automated pipelines).

## Additional resources

- For longer examples (e.g. api_request tool, multi-tool client), see [reference.md](reference.md).
- For project-specific prompts, see [agent_core/agent_core/agents/meta-prompts/claude-agent-sdk.md](agent_core/agent_core/agents/meta-prompts/claude-agent-sdk.md).
