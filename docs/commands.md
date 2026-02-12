# `ai_assist`

CLI tool to manage AI Assistant workspaces.

**Usage**:

```console
$ ai_assist [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `init`: Initialize a new AI Assistant workspace.
* `run`: Start backend and frontend services.
* `workspace`: Workspace management commands
* `global`: Global resources management
* `knowledge`: Knowledge base management
* `note`: Customer note commands

## `ai_assist init`

Initialize a new AI Assistant workspace.

Creates:
- ~/.ai_assist/: Global directory for cross-workspace resources
  - prompts/: Shared prompt templates
  - agents/: Agent definitions
  - tools/: Shared tool definitions
  - models/: Model configurations
  - cache/: Shared cache

- &lt;workspace&gt;/: Local workspace directory
  - data/chroma/: Vector database
  - prompts/: Local prompt templates
  - tools/: Local tool definitions
  - history/: Chat history
  - summaries/: Conversation summaries
  - notes/: Documents for RAG

**Usage**:

```console
$ ai_assist init [OPTIONS] [PATH]
```

**Arguments**:

* `[PATH]`: Path where to create the workspace. Defaults to current directory.

**Options**:

* `-n, --name TEXT`: Workspace name. Defaults to directory name.
* `-f, --force`: Overwrite existing workspace configuration.
* `--help`: Show this message and exit.

## `ai_assist run`

Start backend and frontend services.

By default, uses Docker Compose to start services with pre-built images.
Use --dev flag to run services directly using uv and npm (development mode).

The command will auto-detect the workspace by looking for the workspace marker
in the current directory or parent directories. You can also specify a workspace path.

**Usage**:

```console
$ ai_assist run [OPTIONS] [WORKSPACE_PATH]
```

**Arguments**:

* `[WORKSPACE_PATH]`: Path to workspace. Defaults to current directory (auto-detected).

**Options**:

* `-d, --dev`: Run in development mode (uses uv and npm instead of Docker).
* `--help`: Show this message and exit.

## `ai_assist workspace`

Workspace management commands

**Usage**:

```console
$ ai_assist workspace [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `status`: Show workspace status and directory summary.
* `clean`: Clean workspace data (history, summaries,...
* `list`: List all known workspaces.

### `ai_assist workspace status`

Show workspace status and directory summary.

**Usage**:

```console
$ ai_assist workspace status [OPTIONS] [PATH]
```

**Arguments**:

* `[PATH]`: Path to workspace. Defaults to current directory.

**Options**:

* `--help`: Show this message and exit.

### `ai_assist workspace clean`

Clean workspace data (history, summaries, cache).

**Usage**:

```console
$ ai_assist workspace clean [OPTIONS] [PATH]
```

**Arguments**:

* `[PATH]`: Path to workspace. Defaults to current directory.

**Options**:

* `-y, --yes`: Skip confirmation prompt.
* `--help`: Show this message and exit.

### `ai_assist workspace list`

List all known workspaces.

**Usage**:

```console
$ ai_assist workspace list [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `ai_assist global`

Global resources management

**Usage**:

```console
$ ai_assist global [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `status`: Show global AI Assist home status.
* `config`: Display global configuration file.
* `prompts`: List available global prompts.
* `agents`: List available global agents.
* `tools`: List available global tools.
* `tree`: Show the global directory structure.

### `ai_assist global status`

Show global AI Assist home status.

**Usage**:

```console
$ ai_assist global status [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `ai_assist global config`

Display global configuration file.

**Usage**:

```console
$ ai_assist global config [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `ai_assist global prompts`

List available global prompts.

**Usage**:

```console
$ ai_assist global prompts [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `ai_assist global agents`

List available global agents.

**Usage**:

```console
$ ai_assist global agents [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `ai_assist global tools`

List available global tools.

**Usage**:

```console
$ ai_assist global tools [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

### `ai_assist global tree`

Show the global directory structure.

**Usage**:

```console
$ ai_assist global tree [OPTIONS]
```

**Options**:

* `--help`: Show this message and exit.

## `ai_assist knowledge`

Knowledge base management

**Usage**:

```console
$ ai_assist knowledge [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `process`: Process knowledge documents from a JSON...
* `stats`: Show RAG vector store statistics.

### `ai_assist knowledge process`

Process knowledge documents from a JSON specification file.

The JSON file should contain an array of document specifications:

[
  {&quot;document_type&quot;: &quot;website&quot;, &quot;uri&quot;: &quot;https://...&quot;, &quot;collection&quot;: &quot;flink&quot;},
  {&quot;document_type&quot;: &quot;folder&quot;, &quot;uri&quot;: &quot;$HOME/docs&quot;, &quot;collection&quot;: &quot;python&quot;}
]

Supported document_type values: website, folder, markdown

The &#x27;collection&#x27; field is mapped to &#x27;category&#x27; in the backend for filtering.
Environment variables ($HOME) and ~ are expanded in URIs.

**Usage**:

```console
$ ai_assist knowledge process [OPTIONS] JSON_FILE
```

**Arguments**:

* `JSON_FILE`: Path to JSON file containing document specifications.  [required]

**Options**:

* `-b, --backend-url TEXT`: Backend API URL. Defaults to AI_ASSIST_BACKEND_URL env var or http://localhost:8000/api
* `-n, --dry-run`: Validate JSON and show what would be processed without making API calls.
* `-f, --force`: Force re-indexing even if content unchanged.
* `-v, --verbose`: Show detailed output including errors.
* `--help`: Show this message and exit.

### `ai_assist knowledge stats`

Show RAG vector store statistics.

**Usage**:

```console
$ ai_assist knowledge stats [OPTIONS]
```

**Options**:

* `-b, --backend-url TEXT`: Backend API URL. Defaults to AI_ASSIST_BACKEND_URL env var or http://localhost:8000/api
* `--help`: Show this message and exit.

## `ai_assist note`

Customer note commands

**Usage**:

```console
$ ai_assist note [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `parse`: Parse a customer note markdown file and...

### `ai_assist note parse`

Parse a customer note markdown file and create organization, project, persons, and meeting refs.

The file should follow a structure like: H1 = org name, ## Team / ## &lt;Org&gt; = people,
## Products/Context/Technology stack = context, ## Past steps/Next steps = steps,
## Discovery call/Questions = meeting sections. Uses an LLM to extract structured
data and optionally creates entities via the backend API.

**Usage**:

```console
$ ai_assist note parse [OPTIONS] FILE_PATH
```

**Arguments**:

* `FILE_PATH`: Path to customer note markdown file (e.g. index.md).  [required]

**Options**:

* `-b, --backend-url TEXT`: Backend API URL. Defaults to AI_ASSIST_BACKEND_URL or http://localhost:8000/api
* `-n, --dry-run`: Only parse and show extracted data; do not call the backend.
* `-v, --verbose`: Show detailed output.
* `--help`: Show this message and exit.
