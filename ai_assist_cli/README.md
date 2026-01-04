# AI Assist CLI

Command-line tool for managing AI Assistant's workspaces and global cross workspace, knowledge, notes, history, tools, skills.

## Installation

### Using uv (recommended)

```bash
cd ai_assist_cli
uv pip install -e .
```

### Using pip

```bash
cd ai_assist_cli
pip install -e .
```

## Usage

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

### Configuration management

```bash
# Show current configuration
ai_assist config show

# Get a specific value
ai_assist config get llm_provider

# Set a configuration value
ai_assist config set llm_provider openai

# Open config file in editor
ai_assist config edit
```

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

Each workspace has its own local structure:

```
my-workspace/
├── config.yaml          # Workspace configuration
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

Default settings used across workspaces:

```yaml
version: "1.0"
default_llm_provider: ollama
default_llm_model: gpt-oss:20b
default_llm_base_url: http://localhost:11434
default_embedding_model: all-MiniLM-L6-v2
```

### Workspace Configuration

Each workspace has its own `config.yaml`:

```yaml
name: my-workspace
version: "1.0"

# Database
database_path: data/db/assistant.db
database_url: postgresql+asyncpg://postgres:postgres@my-workspace:5432/biz_assistant

# Vector store
chroma_persist_directory: data/chroma
chroma_collection_name: knowledge-base

# LLM settings
llm_provider: ollama
llm_model: gpt-oss:20b
llm_api_key: null
llm_base_url: http://localhost:11434
llm_max_tokens: 2048
llm_temperature: 0.1

# RAG settings
embedding_model: all-MiniLM-L6-v2
chunk_size: 1000
chunk_overlap: 200
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

## Development

```bash
cd ai_assist_cli
uv sync
uv run ai_assist --help
```
