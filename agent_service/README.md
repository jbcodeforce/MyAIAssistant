# Agent Service

Agno + AgentOS microservice for MyAIAssistant: chat, knowledge, RAG, meeting extract, and task tagging. When the backend sets `AGENT_SERVICE_URL`, the frontend calls this service directly for chat and RAG search/stats/delete; the backend still proxies RAG index, meeting extract, and task tag.

The choice of using AgentOS is that it deliver a powerful REST API to be usable by any clients and the frontend.

## Run locally

```bash
cd agent_service
./start_dev_mode.sh
```

## Endpoints (frontend direct or backend proxy)

- `GET /health` – liveness
- `POST /chat/todo` – task-specific chat (body: message, conversation_history, task_title, task_description, use_rag)
- `POST /chat/generic` – generic/routed chat
- `POST /chat/generic/stream` – streaming generic chat (NDJSON)
- `POST /rag/index/{knowledge_id}` – index knowledge (body: title, uri, document_type, content, category, tags)
- `POST /rag/search`, `GET /rag/search` – semantic search
- `GET /rag/stats`, `DELETE /rag/index/{knowledge_id}` – RAG stats and remove index
- `POST /extract/meeting` – extract attendees, next_steps, key_points, cleaned_notes (body: content, organization?, project?, attendees?)
- `POST /tag/task` – suggest tags for a task (body: task_title, task_description)

### CORS

When the frontend calls the agent-service directly (same as when `AGENT_SERVICE_URL` is set), the browser requires CORS. The agent-service allows origins from `CORS_ORIGINS` (default `http://localhost:3000,http://127.0.0.1:3000`). For production, set `CORS_ORIGINS` to your frontend origin(s), e.g. `https://app.example.com`.

## Docker

From repo root:

```bash
docker compose up -d agent-service
```

Or build and run from this directory:

```bash
docker build -t agent-service .
docker run -p 8100:8100 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 agent-service
```

Backend: set `AGENT_SERVICE_URL=http://localhost:8100` (or `http://agent-service:8100` in Compose) to use this service.

## Tests

Integration tests live under `tests/it/` and assert the HTTP contract (paths, request/response shapes, validation).

- **Default (no env):** Tests run against a stub app (no Ollama/Chroma). Fast, no external services.
- **Running server:** Set `AGENT_SERVICE_URL=http://localhost:8100` to hit a running agent-service (no stub).
- **Live (in-process):** Set `AGENT_SERVICE_LIVE=1` to use the real app inside the test process (requires LLM and optionally Ollama for RAG).

```bash
uv sync --extra dev
uv run pytest tests/it -v
```

## Config

| Env | Default | Description |
|-----|---------|-------------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server (chat + embeddings). LLM API at `{OLLAMA_BASE_URL}/v1`. |
| `LOCAL_LLM_BASE_URL` | (derived from `OLLAMA_BASE_URL` + `/v1`) | Override LLM API base URL if different from Ollama. |
| `LOCAL_LLM_MODEL` | `llama3.2` | Ollama model id for chat. |
| `CHROMA_PERSIST_DIRECTORY` | `data/chroma` | Chroma path for RAG |
| `KNOWLEDGE_EMBEDDER_MODEL` | `nomic-embed-text` | Embedder model id |
| `AGENT_DB_PATH` | `data/agents.db` | Sqlite path for agent history |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated origins allowed for browser requests (frontend-direct mode). |
