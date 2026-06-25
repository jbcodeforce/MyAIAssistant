# Agent Management

The agent management UI lists agents from the **agent_service** microservice. The backend proxies `GET /api/myai/agents` using server-side `agent_service_url`.

## Purpose

- Expose which AgentOS agents are available (e.g. MainAgent, TaskAgent).
- Show per-agent metadata from YAML definitions under `agent_service/agent_service/agents/config/`.
- Open chat against a selected agent via the frontend (calls agent_service directly).

## Data Source

- **agent_service**: `AgentFactory` loads agents from package config and optional `AGENT_CONFIG_DIR`.
- **Backend proxy**: [`backend/app/api/myai_agents.py`](../../backend/app/api/myai_agents.py) forwards to `GET /myai/agents` on agent_service.
- **No database**: Agent definitions are YAML files, not PostgreSQL rows.

## Backend API

```http
GET /api/myai/agents
```

Requires `agent_service_url` in backend config. Returns the same JSON array as agent_service `GET /myai/agents`.

## agent_service API

```http
GET /myai/agents
GET http://localhost:8100/agents          # AgentOS discovery
POST http://localhost:8100/agents/{id}/runs
```

Agent YAML lives under `agent_service/agent_service/agents/config/<AgentName>/` (`agent.yaml`, `prompt.md`).

## Frontend

The Agents view (`frontend/src/views/Agents.vue`) calls `agentsApi.list()` which hits `/api/myai/agents`.

## Adding an agent

See [AGENT.md](../../AGENT.md) and `agent_service/README.md`.
