# Implementation Overview

MyAIAssistant is built with a modular architecture separating concerns across distinct components.


## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    Vue.js Frontend                                       │
│  ┌──────────┐ ┌───────────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────────┐  │
│  │Dashboard │ │   Orgs    │ │Projects│ │Knowledge│ │Meetings│ │ Assets │ │Unclassified│  │
│  │ (Matrix) │ │   View    │ │  View  │ │  View   │ │  View  │ │  View  │ │   View     │  │
│  └──────────┘ └───────────┘ └────────┘ └─────────┘ └────────┘ └────────┘ └────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FastAPI Backend                                       │
│  ┌────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐ │
│  │Todo API│ │ Orgs API │ │Projects│ │Knowledge│ │Meetings│ │ Assets │ │    RAG API     │ │
│  └────────┘ └──────────┘ └────────┘ └─────────┘ └────────┘ └────────┘ └────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────┘
                          │                                    │
                          ▼                                    ▼
               ┌──────────────────┐                 ┌──────────────────────┐
               │    PostgreSQL    │                 │       ChromaDB       │
               │  (Relational DB) │                 │    (Vector Store)    │
               └──────────────────┘                 └──────────────────────┘
```


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

### Meeting Notes

Manage meeting notes with organization and project associations. Content is stored in markdown files with metadata tracked in the database.

- Meeting ID-based identification
- Links to organizations and projects
- Markdown content with live preview
- File-based storage with database references

[Learn more about Meeting Notes](meetings.md)

### Assets

Reusable assets developed within projects or tasks. Assets reference code repositories, documents, or other resources.

- Name and description metadata
- Reference URL to external resources
- Links to projects and tasks
- Searchable asset library

[Learn more about Assets](assets.md)

### RAG System

Retrieval-Augmented Generation for semantic search across the knowledge base.

- Document loading and text chunking
- Vector embeddings using sentence-transformers
- ChromaDB for vector storage
- Semantic search with category filtering

[Learn more about RAG System](rag.md)

### Chat

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
│   │       └── schemas/   # Pydantic request/response schemas
│   │   ├── core/          # Configuration management
│   │   ├── db/            # Database models and CRUD operations
│   │   ├── rag/           # RAG service components

│   ├── tests/             # Test suite
├── data/                  # chroma VB persistence
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
| Todos | `/api/todos` | Task management operations |
| Organizations | `/api/organizations` | Organization management |
| Projects | `/api/projects` | Project management |
| Knowledge | `/api/knowledge` | Knowledge item management |
| Meetings | `/api/meeting-refs` | Meeting notes management |
| Assets | `/api/assets` | Reusable asset management |
| RAG | `/api/rag` | Indexing and semantic search |
| Metrics | `/api/metrics` | Dashboard metrics |
| Health | `/health` | Application health check |

## Data Flow

1. **Todo Creation**: Frontend submits todo data via API, stored in SQLite
2. **Knowledge Registration**: User adds knowledge items with URIs pointing to documents
3. **Document Indexing**: RAG service loads documents, chunks text, generates embeddings
4. **Semantic Search**: Query embeddings compared against stored vectors for retrieval
5. **Task Linking**: (Planned) AI matches todos to relevant knowledge items

## Settings

Configuration may be set by user. The app/core/config.py supports a layered configuration:

* Default config (app/config.yaml) - shipped with the app, contains all settings with sensible defaults.
* User config (via CONFIG_FILE env var) - optional, only needs to include settings the user wants to override.
* Priority Order (highest wins)
    * Environment variables
    * .env file
    * User config file (CONFIG_FILE)
    * Default config (app/config.yaml)
    * Pydantic field defaults