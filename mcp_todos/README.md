# MCP server for MyAIAssistant todos

Exposes MyAIAssistant backend todos via the Model Context Protocol so agents (e.g. Cursor) can create and search todos.

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

## Cursor MCP configuration

Add an MCP server in Cursor (Settings > MCP, or `.cursor/mcp.json`) so Cursor can call the tools:

- **Command**: `uv`
- **Args**: `run`, `python`, `-m`, `mcp_todos`
- **Cwd**: Path to the `mcp_todos` directory (e.g. `.../MyAIAssistant/mcp_todos`).
- **Env** (optional): `MYAI_BACKEND_URL=http://localhost:8000` if different from default.

Example `.cursor/mcp.json` (Cursor may use a different format; follow Cursor’s MCP docs):

```json
{
  "mcpServers": {
    "myai-todos": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_todos"],
      "cwd": "/path/to/MyAIAssistant/mcp_todos",
      "env": {}
    }
  }
}
```

If your backend URL is not the default, set `"env": { "MYAI_BACKEND_URL": "http://your-host:8000" }`.

## Troubleshooting (MCP not working in Cursor)

1. **Server not registered**  
   Cursor must have the server in its MCP config. A project-level config is in `MyAIAssistant/.cursor/mcp.json` (command `uv`, args `run`, `python`, `-m`, `mcp_todos`, cwd `mcp_todos`). If you use a different workspace root, add the server via **Cursor Settings > Tools & MCP > Add new MCP server**, or create/edit `~/.cursor/mcp.json` (global) with the same `mcpServers.myai-todos` entry. Use an absolute path for `cwd` if needed (e.g. `/Users/you/MyAIAssistant/mcp_todos`).

2. **Wrong working directory**  
   The server must be run with its working directory set to the `mcp_todos` folder (so `python -m mcp_todos` finds the package). If you use global config, set `cwd` to the full path of `mcp_todos`.

3. **`uv` not on PATH**  
   Cursor runs the command in a shell where `uv` must be available. Install uv and ensure it is on PATH in the environment Cursor uses (e.g. restart Cursor after installing).

4. **Backend not running**  
   The MCP server calls `MYAI_BACKEND_URL` (default `http://localhost:8000`). Start the MyAIAssistant backend first; otherwise tool calls will fail with connection errors.

5. **Restart Cursor**  
   After adding or changing MCP config, fully quit and reopen Cursor so it picks up the new server.

6. **Verify the server runs**  
   In a terminal: `cd mcp_todos && uv run python -m mcp_todos`. You should see "MyAIAssistant todos MCP server starting". Press Ctrl+C to stop. If this fails, fix the environment (uv, Python) before relying on Cursor.

## Tools

- **create_todo**: Create a todo (title required; optional description, category, tags, status, etc.).
- **search_todos**: List/search todos (optional search, status, category, limit, skip).
- **get_todo**: Get one todo by ID.
- **update_todo**: Update a todo by ID.
- **delete_todo**: Delete a todo by ID.
