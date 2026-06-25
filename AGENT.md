# AGENT.md

Guidance for AI coding assistants (Cursor, Claude Code, etc.) working in this repository.

## What this is

MyAIAssistant is a personal productivity and knowledge management application. It combines Eisenhower-matrix todo management, organization/project/meeting tracking, asset management, and LLM-powered chat with RAG over user documents.

The product goal is to connect **tasks**, **customer/org context**, and **knowledge** in one workspace-aware system — not just a chat UI over files.

| Layer | Technology |
| ----- | ---------- |
| Frontend | Vue 3 + Vite + Pinia (port 3000 dev) |
| Backend | FastAPI + SQLAlchemy async (port 8000) |
| Agent microservice | Agno AgentOS (port 8100) |
| CLI | `ai_assist_cli` (Typer + Agno tools) |
| MCP | `mcp_todos` (todo CRUD for Cursor) |
| Database | SQLite (default) or PostgreSQL per workspace |
| Vector store | LanceDB (agent_service) |

Published docs: [MyAIAssistant documentation](https://jbcodeforce.github.io/MyAIAssistant). In-repo detail lives under `docs/`.

## Project layout

```
MyAIAssistant/
├── backend/           # FastAPI app: todos, orgs, projects, meetings, knowledge, RAG proxy
├── frontend/          # Vue SPA; calls backend and (when configured) agent_service directly
├── agent_service/     # Agno + AgentOS microservice — all AI features
├── ai_assist_cli/     # Workspace CLI; Agno agents for notes, org reports, etc.
├── mcp_todos/         # MCP server exposing todo APIs to Cursor
├── workspaces/        # Isolated deployment configs (DB, Chroma, ports)
│   └── km-db/         # Example workspace (km_assistant DB, port 8001)
├── docs/              # MkDocs source
└── docker-compose.yml # backend + agent-service + frontend
```

### Workspace model

Each workspace is a self-contained deployment: its own `config.yaml`, database, vector store, and optional agent configs. Point the backend at a workspace with `CONFIG_FILE`:

```bash
CONFIG_FILE=/path/to/workspaces/km-db/config.yaml uv run uvicorn app.main:app --reload
```

Workspace marker (CLI): `.ai_assist_workspace` JSON file with a `name` field. Typical layout:

```
workspace/
├── .ai_assist_workspace
├── config.yaml              # database_url, chroma paths, llm settings, agent_service_url
├── data/                    # SQLite DB, Chroma, LanceDB
├── notes/                   # Markdown for RAG / org reports
└── logs/
```

Verify which DB the running backend uses: `GET http://localhost:8000/debug/config`.

## Commands

### Full stack (Docker)

```bash
docker compose up -d
# UI: http://localhost:80   Backend: :8000   Agent service: :8100
```

### Local development

```bash
# Backend
cd backend && uv sync && uv run uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Agent service (Agno AgentOS + compatibility routes)
cd agent_service && ./start_dev_mode.sh
# API docs: http://localhost:8100/docs

# MCP todos server (backend must be running)
cd mcp_todos && uv sync && uv run python -m mcp_todos
```

### Tests

```bash
cd backend && uv run pytest
cd agent_service && uv run pytest tests/ut -v
cd agent_service && uv run pytest tests/it -v   # requires agent_service running
cd ai_assist_cli && uv run pytest
```

Integration tests in `agent_service/tests/it/` expect `./start_dev_mode.sh` or equivalent (Ollama, LanceDB paths).

## Architecture

### Request flow

```
Frontend ──► Backend (8000)     todos, orgs, projects, meetings, knowledge metadata
         └──► Agent service (8100)   chat, RAG search/stats, agent runs (when agent_service_url set)
Backend  ──► Agent service         RAG index, meeting extract, task tagging (proxy)
```

When `agent_service_url` is set in backend config, the frontend reads it from `GET /api/config` and calls agent_service directly for chat and RAG search. The backend still proxies indexing (loads document content) and some extract/tag endpoints.

### Domain modules (backend)

| Area | API prefix | Notes |
| ---- | ---------- | ----- |
| Todos | `/api/todos` | Eisenhower matrix, weekly views |
| Organizations | `/api/organizations` | Customers, stakeholders, team |
| Projects | `/api/projects` | Linked to orgs, status lifecycle |
| Meetings | `/api/meeting-refs` | Meeting notes linked to org/project |
| Knowledge | `/api/knowledge` | Metadata records pointing to markdown/website URIs |
| RAG | `/api/rag` | Index via backend proxy to agent_service; search/stats on agent_service |
| Chat | `/api/chat` | Health only; frontend uses agent_service for chat |
| Agents | `/api/myai/agents` | Proxy list from agent_service |

Business logic belongs in services/CRUD, not route handlers. Follow async SQLAlchemy 2.0 patterns throughout.

## AI implementation — agent_service

All LLM, RAG, extract, and tag features run in `agent_service` (Agno + AgentOS). The backend proxies RAG index (after loading document content), meeting extract, and task tagging.

Location: `agent_service/agent_service/`

- **AgentOS** serves agents at `POST /agents/<agentId>/runs` and exposes OpenAPI at `/docs`.
- **AgentFactory** loads YAML from `agent_service/agents/config/` or `AGENT_CONFIG_DIR`.
- **AIAgent** wraps `agno.agent.Agent` with workspace YAML (prompt.md, tools, model, knowledge).
- **Routes**: `routes/chat.py`, `rag.py`, `extract.py`, `tag.py` — compatibility layer for backend/frontend.
- **Tools**: `tools/backend_tools.py` (todo/project REST tools), customer import/normalize CLIs.
- **Persistence**: SQLite via `ai_db.py` (Agno sessions/memory); LanceDB at `VS_DB_URL` for vectors.

Default agents today: `MainAgent`, `TaskAgent` under `agents/config/`.

Key env vars:

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local LLM |
| `LLM_BASE_URL` | `{OLLAMA}/v1` | OpenAI-compatible chat API |
| `LLM_MODEL` | `llama3.2` | Chat model id |
| `VS_DB_URL` | `data/vs.db` | LanceDB path |
| `AGENT_DB_PATH` / `AI_DB_FILE` | `data/agents.db` | Agno session DB |
| `AGENT_CONFIG_DIR` | package `agents/config` | YAML agent definitions |
| `CORS_ORIGINS` | localhost:3000 | Required for frontend-direct mode |

### `ai_assist_cli` — Agno at the CLI boundary

Standalone Typer CLI using Agno agents (note parsing, org challenges report). Uses SQLAlchemy sync URLs for read-only DB tools against the workspace database.

## Relationship to km-agent

[km-agent](../km-agent) (`../km-agent` sibling repo) is a focused **study-material → structured wiki → chat** system, also on **Agno AgentOS + PostgreSQL/pgvector**. Use it as the reference implementation for advanced agent patterns you may port here.

| Concept (km-agent) | km-agent location | MyAIAssistant equivalent / gap |
| ------------------ | ----------------- | ------------------------------ |
| Coordinating Team | `src/kma/agents/team.py` | No Team yet; `MainAgent` + router/classifier patterns |
| Navigator | `navigator.py` | Chat + RAG search; no wiki index-first routing |
| Compiler | `compiler.py` | No raw→wiki pipeline |
| Researcher | `researcher.py` | No web ingest agent (ParallelTools) |
| Linter | `linter.py` | No wiki health agent |
| Tool assembly | `src/kma/tools/builder.py` | `backend_tools.py` + Agno tool lists in YAML |
| Knowledge pipeline | `context/raw/` → `context/wiki/` | Knowledge items + RAG index only |
| Vector search | pgvector hybrid (kma schema) | ChromaDB / LanceDB |
| LLM providers | `config.py`, `llm_factory.py` | OpenAI-like endpoint env vars; less provider abstraction |
| Workspace context | `context/` tree | Per-workspace `notes/`, `data/`, config.yaml |

**When porting km-agent work:**

1. Add agents under `agent_service/agent_service/agents/config/<AgentName>/` (`agent.yaml` + `prompt.md`) before writing custom Python classes.
2. Custom workflow agents (Team, multi-step compile) go in `agent_service/agent_service/agents/` extending `AIAgent` / `agno.agent.Agent`.
3. Centralize tool wiring (km-agent's `tools/builder.py` pattern) — avoid scattering tool registration across agent files.
4. Register new agents in AgentFactory discovery and mount on AgentOS in `main.py`.
5. Expose HTTP via AgentOS runs or add compatibility routes if the frontend/backend expect fixed paths.
6. For wiki-style knowledge (raw manifest, incremental compile, index.md routing), plan new workspace directories under `notes/` or a dedicated `wiki/` tree — do not assume the current Knowledge model is sufficient.
7. If adopting pgvector hybrid search like km-agent, that is a cross-cutting change (Postgres workspace + embedder dimensions); today vector storage is Chroma/Lance.

Read km-agent's `docs/SPEC.md` and `CLAUDE.md` for pipeline semantics before implementing Compiler/Navigator equivalents.

## Adding a new agent (agent_service)

1. Create `agent_service/agent_service/agents/config/MyAgent/agent.yaml` and `prompt.md`.
2. Optional `class:` in YAML for custom Python (`agent_service/agents/my_agent.py`).
3. List tools by name if registered in `TASK_PROJECT_TOOL_REGISTRY` (`backend_tools.py`).
4. Restart agent_service; confirm via `GET http://localhost:8100/agents`.
5. Add integration test under `agent_service/tests/it/` if HTTP contract matters.

Example YAML shape:

```yaml
name: MyAgent
description: Short purpose
agent_class: agent_service.agents.base_ai_agent.AIAgent
model: llama3.2
tools:
  - list_todos
  - search_knowledge
```

## Configuration priority

Backend settings (highest first):

1. Environment variables
2. `.env`
3. `CONFIG_FILE` YAML (workspace)
4. `backend/app/config.yaml` defaults

Important backend keys: `database_url`, `agent_service_url`, `notes_root`, `llm_*`.

## Gotchas

- **agent_service_url required**: Backend AI endpoints return 503 if unset; frontend reads URL from `GET /api/config`.
- **Frontend dual mode**: Chat and RAG search call agent_service directly when `agent_service_url` is set.
- **DB path vs running server**: SQLite files under `workspaces/*/data/` only reflect UI changes if `CONFIG_FILE` points there and uvicorn cwd resolves relative paths correctly.
- **Ollama on host**: Docker Compose reaches it via `host.docker.internal:11434`, not a containerized Ollama service.
- **Embedding dimensions**: Changing embedder model may require re-indexing or wiping LanceDB (`VS_DB_URL`).

## Cursor rules in this repo

Module-specific rules live in `.cursor/rules/`:

| Rule | Scope |
| ---- | ----- |
| `backend.mdc` | FastAPI, SQLAlchemy, agent_service proxy |
| `frontend.mdc` | Vue 3, Pinia, API client |
| `ai_assist_cli.mdc` | CLI commands and workspace services |
| `tdd.mdc` | Test-driven development expectations |
| `build.mdc` | Checkpoint commits, verification commands |
| `writing.mdc` | Markdown style (no emojis, concise technical tone) |

Prefer those rules when editing files they glob-match.

## Key reference files

| Topic | Path |
| ----- | ---- |
| Agent service overview | `agent_service/README.md` |
| Agent UI/API | `docs/implementation/agents.md` |
| Knowledge model | `docs/implementation/knowledge.md` |
| Deployment / config | `docs/deployment/configuration.md` |
| MCP todos | `mcp_todos/README.md` |
| km-agent spec (porting source) | `../km-agent/docs/SPEC.md` |
| km-agent dev guide | `../km-agent/CLAUDE.md` |

## What not to assume

- Chat architecture docs under `docs/implementation/chat.md` are partly **planned**; runtime behavior follows agent_service + backend proxy code.
- Not every workspace in `workspaces/` is fully populated in git (some are local-only deployment configs).
