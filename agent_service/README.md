# Agent Service

Agno + AgentOS microservice for MyAIAssistant: chat, knowledge, RAG, meeting extract, and task tagging. When the backend sets `AGENT_SERVICE_URL`, the frontend calls this service directly for chat and RAG search/stats/delete; the backend still proxies RAG index, meeting extract, and task tag.

The choice of using AgentOS is that it deliver a powerful REST API to be usable by any clients and the frontend.

## Implementation approach

The agents, teams and workflows are defined in yaml, with their prompt and use generic code with knowledge, database, and reasoning.

The Agno Agents are wrapped by AIAgent, to map the loaded configuration from the Yaml.

The general purpose agent is the base_ai_agent. It has tooks to search the web, knowledge and reasoning capability.

## Run locally

```bash
cd agent_service
./start_dev_mode.sh
```

## Endpoints (frontend direct or backend proxy)

- `GET /health` – liveness
- `POST /agents/agentId/runs`

Backend: set `AGENT_SERVICE_URL=http://localhost:8100` (or `http://agent-service:8100` in Compose) to use this service.

## Tests

Integration tests live under `tests/it/` and assert the HTTP contract (paths, request/response shapes, validation). They use httpx client, so the agent_service server needs to run.

```bash
uv sync --extra dev
uv run pytest tests/it -v
```

## Config

| Env | Default | Description |
|-----|---------|-------------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server (chat + embeddings). LLM API at `{OLLAMA_BASE_URL}/v1`. |
| `VS_DB_URL` | `data/vs.db` | LanceDB path for RAG vectors |
| `KNOWLEDGE_EMBEDDER_MODEL` | `nomic-embed-text` | Embedder model id |
| `AGENT_DB_PATH` | `data/agents.db` | Sqlite path for agent history |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated origins allowed for browser requests (frontend-direct mode). |

