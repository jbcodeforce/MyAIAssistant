# Agent Frontend Fix Plan

## Overview

The agent service is a FastAPI application built on Agno AgentOS.
The Vue 3 frontend connects to it directly via an `agent_service_url` config value.

Several protocol and configuration mismatches prevent correct end-to-end operation:

1. **AgentOS runs endpoint** accepts `application/x-www-form-urlencoded`; the frontend sends JSON.
2. **Streaming protocol mismatch**: the frontend reads NDJSON but native AgentOS uses SSE.
3. **Per-agent YAML model config is ignored**: `AIAgent._build_model()` always reads env vars.
4. **Agent URL shape** for streaming is wrong: the factory generates `.../runs`, the frontend appends `/stream` producing `.../runs/stream`, which does not exist.
5. **Integration tests** have no live-server coverage for the SSE streaming path against a real LLM (omlx at `http://10.0.0.148/v1`).

Goal: fix all mismatches, make the per-agent model config effective, and add integration tests that verify the full end-to-end path with the omlx LLM server.

---

## Sub-Task 1 — Backend: accept JSON on the AgentOS runs endpoint

**Status:** `[ ] pending`

### Intent
AgentOS registers `/agents/{name}/runs` and accepts only form-encoded bodies.
The frontend posts JSON. Rather than modifying the frontend or the Agno internals,
add a thin FastAPI middleware/route that accepts `application/json` and re-dispatches
it as `application/x-www-form-urlencoded` to the AgentOS handler.

### Expected Outcomes
- `POST /agents/{name}/runs` with `Content-Type: application/json` body `{"message":"...", "stream":true, "session_id":"..."}` returns a valid response.
- Existing form-encoded integration tests (`test_agent_service.py`) still pass.

### Todo List
1. Read `agent_service/agent_service/routes/myai_agent_api.py` and `main.py` to understand how routes are mounted.
2. Add a new route (or middleware) in `myai_agent_api.py` (or a new `agents.py` router) that:
   - Matches `POST /agents/{agent_name}/runs`.
   - If `Content-Type` is `application/json`, parses the JSON body, re-encodes it as form data, and forwards to the AgentOS internal handler via `httpx` sub-request (to `http://127.0.0.1:{port}/agents/{agent_name}/runs`).
3. Register the new router **before** the AgentOS app mount so it takes priority.
4. Add a unit test in `tests/ut/` that confirms a JSON body on `/agents/MainAgent/runs` yields HTTP 200.

### Relevant Context
- `agent_service/agent_service/main.py` — app assembly, AgentOS mount
- `agent_service/agent_service/routes/myai_agent_api.py` — existing agent metadata routes
- `agent_service/tests/it/test_agent_service.py:47-51` — existing form-encoded IT test

---

## Sub-Task 2 — Backend: fix per-agent model/temperature/max_tokens from YAML

**Status:** `[ ] pending`

### Intent
`AIAgent._build_model()` currently calls `get_llm_base_url()` and `get_llm_model()`
(both read environment variables) and hard-codes `temperature=0.2`.
The per-agent `agent.yaml` already specifies `model`, `temperature`, and `max_tokens`
but these values are never used. YAML fields should override env vars.

### Expected Outcomes
- `MainAgent` is built with `model=gemma4:31b`, `temperature=0.4`, `max_tokens=100000`.
- `TaskAgent` is built with `model=gemma4:31b`, `temperature=0.6`, `max_tokens=4096`.
- If the YAML field is absent, the env-var default is used as fallback.

### Todo List
1. Read `agent_service/agent_service/agents/base_ai_agent.py` fully.
2. Read `agent_service/agent_service/agents/agent_config.py` fully.
3. Read `agent_service/agent_service/agents/task_agent.py` fully.
4. In `base_ai_agent.py`, update `_build_model()` to accept `config: AgentConfig` and use `config.model`, `config.temperature`, `config.max_tokens` (falling back to `get_llm_model()` / env defaults when the field is `None`).
5. Apply the same change to `task_agent.py` — it already reads `self._config.model` and `self._config.temperature` correctly; verify `max_tokens` is wired to agno's `OpenAILike` `max_tokens` kwarg.
6. Update `AgentConfig` in `agent_config.py` if `max_tokens` or `temperature` fields are missing from the model.
7. Add/update unit tests in `tests/ut/test_agent_service.py` to assert the model `id` matches the YAML value.

### Relevant Context
- `agent_service/agent_service/agents/base_ai_agent.py:51-59` — broken `_build_model`
- `agent_service/agent_service/agents/agent_config.py` — `AgentConfig` model and getters
- `agent_service/agent_service/agents/config/MainAgent/agent.yaml` — expected values

---

## Sub-Task 3 — Backend: fix the streaming URL shape in AgentFactory

**Status:** `[ ] pending`

### Intent
`AgentFactory._load_agent_references()` sets the `url` for each agent to
`{AGENT_SERVICE_URL}/agents/{name}/runs`. The frontend then appends `/stream`
producing `.../runs/stream`, which does not exist as an AgentOS route.
The correct AgentOS streaming path is `.../runs` with `stream=true` in the body —
there is no separate `/stream` suffix.

### Expected Outcomes
- The `url` field in the agent reference points to the correct runs endpoint.
- The frontend no longer appends `/stream` — streaming is toggled by the `stream` field in the request body.
- `GET /myai/agents` returns the corrected URL for each agent.

### Todo List
1. Read `agent_service/agent_service/agents/agent_factory.py` fully.
2. Confirm the URL template used in `_load_agent_references()`.
3. Remove or correct any `/stream` suffix logic there; the URL stays as `.../runs`.
4. Read `frontend/src/services/api.js` streaming section (lines 330–401).
5. In `api.js`, for the `agentUrl` path, stop appending `/stream`; send `stream: true` in the JSON body instead; parse the response as SSE (see Sub-Task 4).
6. Update integration test `test_agent_service_api.py` if it checks the URL value.

### Relevant Context
- `agent_service/agent_service/agents/agent_factory.py:88-96` — URL template
- `frontend/src/services/api.js:330-346` — streaming call that appends `/stream`

---

## Sub-Task 4 — Frontend: migrate streaming reader from NDJSON to SSE

**Status:** `[ ] pending`

### Intent
The current streaming reader in `api.js` splits by newline and `JSON.parse`s each line (NDJSON).
Native AgentOS streaming uses Server-Sent Events:

```
event: RunStarted
data: {...}

event: RunContent
data: {"content":"..."}

event: RunCompleted
data: {...}
```

The frontend must use an SSE reader (either native `EventSource` or a manual
`ReadableStream` SSE parser over `fetch`) so it can extract content from
`RunContent` events and signal completion on `RunCompleted`.

### Expected Outcomes
- Streaming chat in `AssistantChatPanel.vue` renders tokens incrementally from `RunContent` events.
- The `onDone` callback is fired on `RunCompleted`.
- The `onError` callback is fired if the stream ends with a `RunError` event or HTTP error.
- The `/chat/generic/stream` NDJSON compatibility endpoint is removed entirely; all streaming paths use SSE.

### Todo List
1. Read `frontend/src/services/api.js` streaming section fully (lines 325–410).
2. Read `frontend/src/components/chat/AssistantChatPanel.vue` to understand `onChunk`, `onDone`, `onError` contract.
3. Write a helper `parseSseStream(response, { onChunk, onDone, onError })` in `api.js` that:
   - Reads the `ReadableStream` from a `fetch` response.
   - Splits on `\n\n` (SSE message boundaries).
   - Parses `event:` and `data:` lines.
   - Calls `onChunk(text)` for each `RunContent` event where `data.content` is non-empty.
   - Calls `onDone(context_used)` on `RunCompleted`.
   - Calls `onError(msg)` on `RunError` or HTTP non-2xx.
4. Replace the NDJSON reader in `genericChatStream` (for both the `agentUrl` path and the `agent_service_url` fallback path) with `parseSseStream`.
5. Remove the `POST /chat/generic/stream` NDJSON route from `routes/chat.py` and its unit test.
6. Verify the `chatApi.sendMessage` (non-streaming) path: AgentOS non-stream runs return `{"content":"..."}` at the top level — confirm the frontend reads the right field.

### Relevant Context
- `frontend/src/services/api.js:330-401` — NDJSON reader to replace
- `agent_service/tests/it/test_agent_service.py:76-100` — reference SSE event sequence
- `frontend/src/components/chat/AssistantChatPanel.vue:283-314`

---

## Sub-Task 5 — Integration tests: live end-to-end against omlx LLM

**Status:** `[x] done`

### Run Command

```bash
# Run live tests against the omlx LLM server (requires a running agent_service instance):
LLM_BASE_URL=http://10.0.0.148/v1 pytest tests/it/test_live_agent.py -m live -v
```

To verify CI skip behaviour (no LLM server needed):
```bash
cd agent_service && .venv/bin/pytest tests/it/test_live_agent.py -v
# → 3 skipped, 0 failed
```

### Intent
Add integration tests that start the full agent service (or hit a running instance)
and exercise the complete request path: JSON body → AgentOS runs endpoint → omlx LLM
at `http://10.0.0.148/v1` → SSE stream back to client.

These tests are skipped unless `LLM_BASE_URL` is set to a reachable LLM server,
so CI runs without the external dependency.

### Expected Outcomes
- `pytest tests/it/ -m live` runs end-to-end against omlx when `LLM_BASE_URL=http://10.0.0.148/v1`.
- Tests cover: JSON-body run (non-streaming), SSE streaming run, and `/myai/agents` URL shape.
- Tests are marked `@pytest.mark.skipif(not LLM_BASE_URL_SET, reason="no live LLM")` so they are safe in CI.

### Todo List
1. Read `agent_service/tests/it/conftest.py` fully.
2. Read `agent_service/tests/it/test_agent_service.py` fully.
3. Add a `live` pytest mark in `pyproject.toml` (or `conftest.py`).
4. Add `LLM_BASE_URL_SET` guard using `os.getenv("LLM_BASE_URL")`.
5. Write `tests/it/test_live_agent.py` with:
   - `test_json_body_run_non_stream` — POST JSON to `/agents/MainAgent/runs` with `stream=false`, assert HTTP 200 and non-empty response content.
   - `test_json_body_run_stream` — POST JSON with `stream=true`, parse SSE, assert `RunContent` events received.
   - `test_myai_agents_url_shape` — GET `/myai/agents`, assert returned URL does not contain `/stream`.
6. Document how to run: `LLM_BASE_URL=http://10.0.0.148/v1 pytest tests/it/ -m live`.

### Relevant Context
- `agent_service/tests/it/conftest.py` — async client fixture
- `agent_service/tests/it/test_agent_service.py` — SSE parse helper `_parse_sse_stream`
- `agent_service/agent_service/agents/agent_config.py` — `LLM_BASE_URL` env var

---

## Implementation Notes

- Sub-Tasks 1, 2, 3 are pure backend and can be done independently.
- Sub-Task 4 depends on Sub-Task 3 (correct URL shape must be in place first).
- Sub-Task 5 depends on Sub-Tasks 1, 3, 4 being done (tests the fixed paths).
- The NDJSON `POST /chat/generic/stream` route and its unit test are removed in ST-4.
- All streaming goes through AgentOS SSE (`/agents/{name}/runs` with `stream=true`).
