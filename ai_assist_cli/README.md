# AI Assist CLI

Command-line tool for managing AI Assistant's workspaces and global cross workspace, knowledge, notes, history, tools, skills.

## Features

The AI Assist CLI provides a comprehensive set of tools for managing AI Assistant workspaces and resources:

### Workspace Management

- **Initialize workspaces**: Create new workspaces with proper directory structure
- **Workspace status**: View workspace name, location, and directory status
- **List workspaces**: Discover and manage all registered workspaces
- **Clean workspace data**: Remove history, summaries, and cache data
- **Auto-detection**: Automatically detect workspace from current directory or parent directories (via workspace marker)

### Service Management

- **Run services**: Start backend and frontend services with a single command
- **Production mode**: Use Docker Compose to run services with pre-built images
- **Development mode**: Run services directly with `uv` and `npm` for hot-reload development
- **Workspace data**: Mount workspace data directory when running with Docker
- **Health checks**: Wait for services to be ready before completing startup

### Knowledge Base Management
- **Process documents**: Index documents from websites, folders, or markdown files
- **Batch processing**: Process multiple documents from JSON specification files
- **Collection management**: Organize documents into collections/categories
- **Statistics**: View RAG vector store statistics (chunks, documents, models)
- **Dry-run mode**: Validate and preview processing without making changes
- **Force re-indexing**: Re-index documents even when content is unchanged

### Global Resources
- **Cross-workspace resources**: Share prompts, agents, tools, and models across workspaces
- **Global configuration**: Set default LLM and embedding settings
- **Agent definitions**: Manage reusable agent configurations
- **Prompt templates**: Create and share prompt templates
- **Tool definitions**: Define and share custom tools

### Developer Experience
- **Rich output**: Beautiful terminal output with colors, tables, and progress indicators
- **Error handling**: Clear error messages and validation
- **Help system**: Comprehensive help text for all commands
- **Flexible paths**: Support for relative and absolute paths
- **Workspace registry**: Track and manage multiple workspaces

## Installation

### Using uv (recommended)

```bash
cd ../agent_core
uv build

cd ai_assist_cli
uv build
uv tool install /Users/jerome/Documents/Code/MyAIAssistant/ai_assist_cli/dist/ai_assist_cli-0.1.0-py3-none-any.whl \
  --with /Users/jerome/Documents/Code/MyAIAssistant/agent_core/dist/agent_core-0.1.0-py3-none-any.whl \
  --force
```

## Usage

```sh
ai_assist --help
```

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

### Running services

The `run` command starts both backend and frontend services. It supports two modes:

#### Production mode (Docker)

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
# Build agent_core first
cd ../agent_core
uv build

# Build and install CLI
cd ../ai_assist_cli
uv build
uv tool install dist/ai_assist_cli-0.1.0-py3-none-any.whl \
  --with ../agent_core/dist/agent_core-0.1.0-py3-none-any.whl \
  --force
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

### Handling agent-core Dependency

Since `agent-core` is not published to PyPI, you have two options:

#### Option 1: Include agent-core in the Package (Recommended)

Copy the `agent_core` code directly into your package or use a build script to include it:

1. **Update pyproject.toml** to remove the local path dependency:
   ```toml
   # Remove or comment out:
   # [tool.uv.sources]
   # agent-core = { path = "../agent_core", editable = true }
   
   # Keep in dependencies (it will be included in the package):
   dependencies = [
       "typer>=0.15.0",
       "rich>=13.0.0",
       "pyyaml>=6.0.0",
       # agent-core will be bundled, so remove from dependencies or mark as optional
   ]
   ```

2. **Include agent_core in the package**: Update `pyproject.toml` to include agent_core files:
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["ai_assist_cli", "agent_core"]
   ```

3. **Copy agent_core during build**: Create a build script or use a tool like `setuptools` to copy agent_core into the package before building.

#### Option 2: Remove agent-core from Dependencies

If you want to make agent-core optional or handle it differently:

1. **Remove from dependencies** in `pyproject.toml`:
   ```toml
   dependencies = [
       "typer>=0.15.0",
       "rich>=13.0.0",
       "pyyaml>=6.0.0",
       # agent-core removed - users must install separately
   ]
   ```

2. **Document installation**: Users will need to install agent-core separately (e.g., from source or a private repository).

**Note**: The current setup uses a local path dependency for development. For PyPI packaging, you'll need to choose one of the above approaches.

### Building the Package

Build source distribution and wheel:

```bash
cd ai_assist_cli

# Clean previous builds
rm -rf dist/ build/ *.egg-info

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
- **"Missing dependencies"**: If agent-core is not bundled, ensure it's installed separately or included in the package
- **Build errors**: Ensure `pyproject.toml` is valid and all dependencies are specified correctly
- **Import errors for agent-core**: Verify that agent-core is either bundled in the package or available in the Python path
