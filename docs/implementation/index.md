# Implementation Overview

MyAIAssistant is built with a modular architecture separating concerns across distinct components.

## System Components

### Todo Management

The core task management system implementing the Eisenhower Matrix (Urgent/Important classification).

- RESTful API for CRUD operations
- Filtering by status, urgency, importance, category
- Canvas view endpoints for matrix quadrants
- SQLAlchemy ORM with async support

[Learn more about Todo Management](todo.md)

### Knowledge Base

Centralized storage for document metadata with support for various document types.

- Markdown files on local filesystem
- Website URLs for reference
- Category and tag-based organization
- Status tracking (active, pending, error, archived)

[Learn more about Knowledge Base](knowledge.md)

### RAG System

Retrieval-Augmented Generation for semantic search across the knowledge base.

- Document loading and text chunking
- Vector embeddings using sentence-transformers
- ChromaDB for vector storage
- Semantic search with category filtering

[Learn more about RAG System](rag.md)

### Chat (Planned)

LLM-powered chat interface for intelligent interactions.

- Action item extraction from meeting notes
- Automatic knowledge-to-task linking
- Local model support via Ollama

[Learn more about Chat](chat.md)

## Project Structure

```
MyAIAssistant/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints (todos, knowledge, rag)
│   │   ├── core/          # Configuration management
│   │   ├── db/            # Database models and CRUD operations
│   │   ├── rag/           # RAG service components
│   │   └── schemas/       # Pydantic request/response schemas
│   ├── tests/             # Test suite
│   └── data/              # ChromaDB persistence
├── frontend/
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── views/         # Page views
│   │   ├── stores/        # Pinia state management
│   │   ├── services/      # API client
│   │   └── router/        # Vue Router configuration
│   └── public/            # Static assets
└── docs/                  # This documentation
```

## API Structure

All backend APIs follow RESTful conventions with versioned endpoints:

| Module | Base Path | Description |
| ------ | --------- | ----------- |
| Todos | `/api/v1/todos` | Task management operations |
| Knowledge | `/api/v1/knowledge` | Knowledge item management |
| RAG | `/api/v1/rag` | Indexing and semantic search |
| Health | `/health` | Application health check |

## Data Flow

1. **Todo Creation**: Frontend submits todo data via API, stored in SQLite
2. **Knowledge Registration**: User adds knowledge items with URIs pointing to documents
3. **Document Indexing**: RAG service loads documents, chunks text, generates embeddings
4. **Semantic Search**: Query embeddings compared against stored vectors for retrieval
5. **Task Linking**: (Planned) AI matches todos to relevant knowledge items

