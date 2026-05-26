# AI Assist CLI

Command-line tool for managing AI Assistant's workspaces and global cross workspace, knowledge, notes, history, tools, skills.

[See design and implementation note](https://jbcodeforce.github.io/MyAIAssistant/implementation/)

## Installation

### Using uv (recommended)

```bash
cd ai_assist_cli
uv build
uv tool install dist/ai_assist_cli-0.1.0-py3-none-any.whl --force
```

## Usage

```sh
ai_assist --help
```

[See the command reference](https://jbcodeforce.github.io/MyAIAssistant/commands)

### Initialize a new workspace

```bash
# Initialize in current directory
ai_assist init

# Initialize in a specific path
ai_assist init /path/to/workspace

# Initialize with a custom name
ai_assist init --name my-assistant /path/to/workspace
```

This creates both:
- A local workspace at the specified path
- A global `~/.ai_assist` directory for cross-workspace resources (if not already present)

### Workspace management

```bash
# Show workspace status
ai_assist workspace status

# List all known workspaces
ai_assist workspace list

# Clean workspace data (history, summaries)
ai_assist workspace clean
```

### Organization-wide challenges report (Agno)

The `org report` command runs an [Agno](https://github.com/agno-agi/agno) agent with read-only SQL tools (SQLAlchemy) against the app database and tools to list and read markdown under the workspace `notes/` directory. It produces a table of **challenges**, **next steps**, and **issues** keyed by account (organization name or top-level notes folder).

Prerequisites:

- A initialized workspace (`.ai_assist_workspace` at the workspace root).
- `LLM_API_KEY`, `LLM_BASE_URL` (or `OLLAMA_BASE_URL`), and `LLM_MODEL` set for an OpenAI-compatible endpoint (same conventions as the MyAI Assistant agent service).
- For database-backed rows: a SQLite file at `data/app.db` under the workspace (default when using Docker Compose: `./data` maps to the backend data directory). Relative `DATABASE_URL` values such as `sqlite+aiosqlite:///./data/app.db` are resolved against the workspace root.

```bash
# Validate configuration without calling the LLM
ai_assist org report --dry-run

# Notes only (no SQLite tools)
ai_assist org report --skip-db

# JSON output
ai_assist org report --json

# Custom database URL (PostgreSQL or absolute SQLite)
ai_assist org report --database-url "postgresql://user:pass@localhost/mydb"

# Custom notes root
ai_assist org report --notes-root /path/to/notes
```

If `data/app.db` is missing and you did not pass `--skip-db`, the command exits with an error.

### Running services

The `run` command starts both backend and frontend services. It supports two modes:

#### With Docker

Runs services using Docker Compose with pre-built images:

```bash
# Run from workspace directory (auto-detects workspace)
ai_assist run

# Run with explicit workspace path
ai_assist run /path/to/workspace
```

This mode:
- Uses Docker Compose to start backend, frontend, and ollama services
- Mounts workspace data directory
- Requires Docker and docker-compose to be installed

#### Development mode

Runs services directly using `uv` and `npm` (similar to `start_dev_mode.sh`):

```bash
# Run in development mode
ai_assist run --dev

# Run with explicit workspace path
ai_assist run --dev /path/to/workspace
```

This mode:
- Starts backend with `uv run uvicorn` (with hot reload)
- Starts frontend with `npm run dev`
- Automatically installs npm dependencies if needed
- Waits for both services to be ready
- Requires `uv`, `node`, and `npm` to be installed

**Service URLs:**
- Frontend: http://localhost:3000 (dev) or http://localhost:80 (Docker)
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Config Debug: http://localhost:8000/debug/config

Press `Ctrl+C` to stop all services.

### Global resources management

```bash
# Show global home status
ai_assist global status

# Show global configuration
ai_assist global config

# List global prompts
ai_assist global prompts

# List global agents
ai_assist global agents

# List global tools
ai_assist global tools

# Show global directory tree
ai_assist global tree
```

## Directory Structure

### Global Home (`~/.ai_assist`)

The global home directory contains resources shared across all workspaces:

```
~/.ai_assist/
├── config.yaml              # Global default configuration
├── workspaces.json          # Registry of known workspaces
├── prompts/                 # Shared prompt templates
│   ├── base_system.md       # Base system prompt
│   ├── coding_assistant.md  # Coding assistant prompt
│   └── research_assistant.md
├── agents/                  # Agent definitions
│   ├── assistant.yaml       # General assistant
│   ├── coder.yaml           # Coding agent
│   └── researcher.yaml      # Research agent
├── tools/                   # Shared tool definitions
├── models/                  # Model configurations
└── cache/                   # Shared cache
```

### Workspace Directory

Each workspace has its own local structure. A workspace is identified by the presence of `.ai_assist_workspace` (marker file with workspace name):

```
my-workspace/
├── .ai_assist_workspace  # Workspace marker (name)
├── data/
│   ├── chroma/          # Vector database storage
│   └── db/              # SQLite database
├── prompts/             # Local prompt templates
│   ├── system.md        # System prompt
│   └── rag.md           # RAG prompt template
├── tools/               # Local tool definitions
├── history/             # Chat history storage
├── summaries/           # Conversation summaries
└── notes/               # Documents for RAG indexing
```

## Configuration

### Global Configuration (`~/.ai_assist/config.yaml`)

Default settings used across workspaces (global home only; workspace settings are agent-based):

```yaml
version: "1.0"
default_llm_provider: ollama
default_llm_model: gpt-oss:20b
default_llm_base_url: http://localhost:11434
default_embedding_model: all-MiniLM-L6-v2
```

## Agent Definitions

Agents are defined in YAML files under `~/.ai_assist/agents/`:

```yaml
name: coder
description: Software development assistant
system_prompt: coding_assistant.md
tools:
  - file_reader
  - code_executor
temperature: 0.3
max_tokens: 4096
```

## Running the CLI

### Development Mode

Run the CLI directly from source using `uv`:

```bash
cd ai_assist_cli
uv sync
uv run ai_assist --help
```

This is useful for:
- Development and testing
- Making changes to the CLI code
- Running without installing the package

### Packaged CLI (After Installation)

After installing the CLI using `uv tool install` (see Installation section), you can run it directly:

```bash
# The CLI is available as a global command
ai_assist --help

# No need for 'uv run' prefix
ai_assist init
ai_assist run --dev
```

The packaged CLI:
- Is installed globally and available in your PATH
- Includes all dependencies
- Can be used from any directory
- Is the recommended way to use the CLI in production

## Development

To develop the CLI:

```bash
cd ai_assist_cli
uv sync
uv run ai_assist --help
```

To build and install:

```bash
cd ai_assist_cli
uv build
uv tool install dist/ai_assist_cli-0.1.0-py3-none-any.whl --force
```

## Packaging for PyPI

### Prerequisites

Before publishing to PyPI, ensure you have:

1. **PyPI account**: Create an account at [pypi.org](https://pypi.org) (and [test.pypi.org](https://test.pypi.org) for testing)
2. **API tokens**: Generate API tokens from your PyPI account settings
3. **Build tools**: Install build and publish tools:
   ```bash
   uv pip install build twine
   ```

### PyPI dependencies

The CLI depends on standard published packages (Typer, Rich, Agno, SQLAlchemy, Pydantic, and so on). It does not bundle or require a local `agent_core` install.

### Building the Package

Build source distribution and wheel:

```bash
cd ai_assist_cli

# Clean previous builds
rm -rf dist/ 

# Build package
uv build

# Verify built files
ls -lh dist/
# Should show: ai-assist-cli-0.1.0-py3-none-any.whl and .tar.gz
```

### Testing the Build Locally

Test the built package before publishing:

```bash
# Install from local wheel
uv pip install dist/ai_assist_cli-0.1.0-py3-none-any.whl

# Test the CLI
ai_assist --help

# Uninstall when done testing
uv pip uninstall ai-assist-cli
```

### Publishing to PyPI

#### 1. Test PyPI (Recommended First Step)

Publish to Test PyPI to verify everything works:

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation from Test PyPI
uv pip install --index-url https://test.pypi.org/simple/ ai-assist-cli
```

#### 2. Production PyPI

Once tested, publish to production PyPI:

```bash
# Upload to PyPI
twine upload dist/*

# Users can now install with:
pip install ai-assist-cli
# or
uv pip install ai-assist-cli
```

### Authentication

You can authenticate using:

1. **API Token** (recommended): Set environment variable or use `--username __token__ --password <token>`
   ```bash
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-<your-token>
   twine upload dist/*
   ```

2. **Username/Password**: Use `--username` and `--password` flags
   ```bash
   twine upload --username <username> --password <password> dist/*
   ```

3. **Interactive**: Twine will prompt for credentials if not provided

### Version Management

Update version in `pyproject.toml` before each release:

```toml
[project]
version = "0.1.1"  # Increment version number
```

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Post-Publication

After publishing:

1. **Verify installation**: Test installation from PyPI
   ```bash
   pip install ai-assist-cli
   ai_assist --help
   ```

2. **Create GitHub release**: Tag the release and create release notes

3. **Update documentation**: Update any installation instructions to reference PyPI

### Troubleshooting

- **"Package already exists"**: Version already published - increment version number
- **"Invalid distribution"**: Check that all required files are included in the package
- **"Missing dependencies"**: Run `uv sync` (or `pip install -e .`) so declared packages resolve from PyPI
- **Build errors**: Ensure `pyproject.toml` is valid and all dependencies are specified correctly
- **Import errors for Agno/OpenAI**: Ensure `openai` is installed (declared dependency); check your virtual environment
