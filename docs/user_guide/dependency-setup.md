# Dependency Setup

The dependent libraries and tools necessary can be installed with the `.install.sh` tool.

## Prerequisites

- **Python 3.11+** and **uv** (recommended), or **Docker** and **Docker Compose**
- For development mode: **Node.js 18+** and **npm**

## Step 1: Install the ai_assist CLI

From the project root, build and install the CLI (and its dependency `agent_core`):

```bash
cd agent_core
uv build

cd ../ai_assist_cli
uv build
uv tool install ./dist/ai_assist_cli-0.1.0-py3-none-any.whl \
  --with ../agent_core/dist/agent_core-0.1.0-py3-none-any.whl \
  --force
```

Verify the installation:

```bash
ai_assist --help
```

## Step 2: Initialize a workspace

Create a workspace where your data, knowledge, and chat history will live:

```bash
# In the directory you want as your workspace
ai_assist init

# Or specify a path and optional name
ai_assist init /path/to/workspace
ai_assist init --name my-assistant /path/to/workspace
```

This creates:

- A local workspace (with `.ai_assist_workspace`, `data/`, `config/`, etc.)
- A global `~/.ai_assist` directory for shared resources, if it does not exist yet

## Step 3: Run the application

Start the backend and frontend from your workspace:

**Production (Docker):**

```bash
cd /path/to/your/workspace
ai_assist run
```

**Development (local with hot reload):**

```bash
cd /path/to/your/workspace
ai_assist run --dev
```

When services are ready:

| Service   | URL                        |
| --------- | -------------------------- |
| Frontend  | http://localhost:3000 (dev) or http://localhost:80 (Docker) |
| Backend   | http://localhost:8000      |
| API docs  | http://localhost:8000/docs |

Press `Ctrl+C` to stop all services.

## Step 4: (Optional) Check workspace and global resources

```bash
# Workspace status
ai_assist workspace status

# List registered workspaces
ai_assist workspace list

# Global shared resources (prompts, agents, tools)
ai_assist global status
ai_assist global tree
```

## Next steps

- Add more steps here as you extend the guide (e.g. indexing knowledge, configuring agents).
- See [User Guide](index.md) for the full workflow: organizations, projects, tasks, and knowledge base.
- For all CLI commands and options, see the `ai_assist_cli/README.md` file in the repository.
