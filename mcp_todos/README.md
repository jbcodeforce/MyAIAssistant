# MCP server for MyAIAssistant todos

Exposes MyAIAssistant backend todos via the Model Context Protocol so agents (e.g. Claude Code, Pi) can create and search todos.

## Prerequisites

- MyAIAssistant backend running (default: `http://localhost:8000`).
- Python 3.12+ and uv.

## Setup

From the `mcp_todos` directory:

```bash
uv sync
```

## Run

```bash
uv run python -m mcp_todos
```

## Configuration

- **MYAI_BACKEND_URL**: Backend base URL (default: `http://localhost:8000`). Set this if the backend runs on another host or port.

## MCP client configuration

The server speaks MCP over stdio. Using `uv run --directory <path>` keeps the definition portable across clients (no per-client working-directory field needed). Use an absolute path to the `mcp_todos` directory.

Standard stdio server definition:

```json
{
  "mcpServers": {
    "myai-todos": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/MyAIAssistant/mcp_todos", "python", "-m", "mcp_todos"],
      "env": {}
    }
  }
}
```

If your backend URL is not the default, set `"env": { "MYAI_BACKEND_URL": "http://your-host:8000" }`.

### Claude Code

Either add a project-scoped `.mcp.json` at the repo root with the definition above (shared via git), or register it with the CLI:

```bash
claude mcp add myai-todos -- uv run --directory /path/to/MyAIAssistant/mcp_todos python -m mcp_todos
# with a non-default backend:
claude mcp add myai-todos --env MYAI_BACKEND_URL=http://your-host:8000 -- \
  uv run --directory /path/to/MyAIAssistant/mcp_todos python -m mcp_todos
```

Verify with `claude mcp list`.

### Pi

Add the same server definition to Pi's MCP configuration (see Pi's MCP docs for the exact file/location), then reload Pi.

## Troubleshooting (MCP server not available)

1. **Server not registered** — Confirm the client lists `myai-todos` (for Claude Code, `claude mcp list`). Re-add it with the definition above if missing.

2. **Wrong working directory** — `python -m mcp_todos` must run from the `mcp_todos` folder. The `uv run --directory /abs/path/to/mcp_todos` form handles this regardless of where the client launches the command.

3. **`uv` not on PATH** — The client runs the command in its own shell; `uv` must be installed and on PATH there. Reload/restart the client after installing uv.

4. **Backend not running** — The MCP server calls `MYAI_BACKEND_URL` (default `http://localhost:8000`). Start the MyAIAssistant backend first; otherwise tool calls fail with connection errors.

5. **Reload after config changes** — Restart or reload the client so it picks up the new or changed server.

6. **Verify the server runs standalone** — In a terminal: `cd mcp_todos && uv run python -m mcp_todos`. You should see "MyAIAssistant todos MCP server starting". Press Ctrl+C to stop. If this fails, fix the environment (uv, Python) before wiring it into a client.

## Tools

- **create_todo**: Create a todo (title required; optional description, category, tags, status, etc.).
- **search_todos**: List/search todos (optional search, status, category, limit, skip).
- **get_todo**: Get one todo by ID.
- **update_todo**: Update a todo by ID.
- **delete_todo**: Delete a todo by ID.
