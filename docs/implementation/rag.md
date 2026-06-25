# RAG System

The Retrieval-Augmented Generation (RAG) system enables semantic search across the knowledge base using vector embeddings.

**Runtime split (agent_service only):**

| Operation | Caller | Handler |
|-----------|--------|---------|
| Index document | Frontend → Backend `POST /api/rag/index/{id}` | Backend loads content via `DocumentLoader`, proxies to agent_service `POST /rag/index` |
| Search / stats / delete | Frontend → agent_service | `agent_service/routes/rag.py` + Chroma via Agno Knowledge |
| Chat with RAG context | Frontend → agent_service | AgentOS agents |

Backend requires `agent_service_url`. When unset, AI endpoints return HTTP 503. In-process Chroma in the backend was removed with `agent_core`.

## Components

### Document loader (backend)

`backend/app/services/document_loader.py` loads content before indexing:

```python
from app.services.document_loader import DocumentLoader

loader = DocumentLoader(timeout=30.0)
documents = await loader.load(uri, document_type)
```

Supported sources:

| Type | Description | Example URI |
| ---- | ----------- | ----------- |
| markdown | Local or remote markdown files | `file:///path/to/doc.md` or `https://...` |
| website | Web page content (HTML parsed to markdown) | `https://example.com/page` |
| folder | Directory of markdown files | `/path/to/docs/` |

### Vector store and search (agent_service)

Indexing, embedding, chunking, and search run in `agent_service/`:

- `agent_service/knowledge.py` — singleton Agno Knowledge base
- `agent_service/routes/rag.py` — HTTP routes for index, search, stats, delete

Configure Chroma and embedder via agent_service env (see `agent_service/README.md`).

## Backend API (index only)

```http
POST /api/rag/index/{knowledge_id}
POST /api/rag/index-all
```

Both require `agent_service_url`. The backend updates knowledge metadata, loads document content, and POSTs to agent_service.

Legacy backend routes for search, stats, and delete return 503 with a message to use agent_service directly.

## agent_service API

```http
POST /rag/index
GET  /rag/search?q=...&n=5
GET  /rag/stats
DELETE /rag/{knowledge_id}
```

The frontend reads `agent_service_url` from `GET /api/config` and calls these when configured.

## Indexing flow

1. User triggers index from the Knowledge UI.
2. Frontend calls `POST /api/rag/index/{id}` on the backend.
3. Backend loads content with `DocumentLoader`.
4. Backend proxies payload to agent_service `POST /rag/index`.
5. agent_service chunks, embeds, and stores vectors in Chroma.
6. Backend updates knowledge item status (`indexed` or `error`).

## Testing

See [RAG testing](../testing/rag_testing.md). Unit tests mock `agent_service_client.rag_index`. Integration tests require a running agent_service.

## References

- [Knowledge management](knowledge.md)
- [agent_service README](../../agent_service/README.md)
- [AGENT.md](../../AGENT.md)
