# MyAIAssistant Detailed Project Structure

This structure separates the frontend and backend into distinct services, which is ideal for decoupling, scalability, and independent development.

## 1. Top-Level Structure

```
MyAIAssistant/
├── backend/                  # Python FastAPI application
├── frontend/                 # Vue.js application
├── docs/                     * mkdocs project documentation
└── data_scripts/             # Utilities for initial data loading/processing
```

## 2. Frontend (Vue.js) Structure

The frontend is responsible for the user interface, routing, and state management. Assuming Pinia for state management.

```
frontend/
├── src/
│   ├── assets/               # CSS, images, and static resources
│   │   └── styles/           # Global styles and utility CSS
│   ├── components/
│   │   ├── todo/             # Components for Todo management
│   │   │   ├── TodoCanvas.vue      # The main drag-and-drop canvas view
│   │   │   ├── TodoCard.vue        # Individual Todo items
│   │   │   └── StatusIndicator.vue # State (Open, Started, Completed, etc.)
│   │   ├── knowledge/        # Components for Knowledge Management
│   │   │   ├── ReferenceCard.vue   # Cards for documents/links
│   │   │   ├── KnowledgeGraph.vue  # Component for visualizing subject relationships
│   │   │   └── SearchBar.vue       # Semantic search input
│   │   └── common/           # Generic UI components
│   │       ├── Header.vue
│   │       └── Modal.vue
│   ├── services/             # API interaction wrappers
│   │   └── api.js            # Axios/Fetch setup for connecting to the FastAPI backend
│   ├── stores/               # Pinia store modules for state management
│   │   ├── todoStore.js      # Todos, categories, history
│   │   ├── knowledgeStore.js # References, websites, notes, subject relationships
│   │   └── uiStore.js        # UI state (e.g., active view, modals)
│   ├── views/                # Top-level pages/routes
│   │   ├── Dashboard.vue     # Main Todo canvas (Urgent/Important)
│   │   ├── KnowledgeBase.vue # Central view for all knowledge and semantic search
│   │   ├── MeetingNotes.vue  # Interface for viewing/managing notes/transcripts
│   │   └── Unclassified.vue  # Unclassified todos sorted by date
│   ├── router/
│   │   └── index.js
│   ├── App.vue               # Main application component
│   └── main.js               # App entry point
├── package.json
└── vite.config.js
```

## 3. Backend (FastAPI) Structure

The backend handles persistence, data processing, LLM/Vector DB orchestration, and core business logic.

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI entry point, CORS, startup/shutdown events
│   ├── api/                  # API routers (endpoints)
│   │   ├── v1/
│   │   │   ├── todos.py          # CRUD for todos, state updates, history
│   │   │   ├── knowledge.py      # CRUD for references, websites, subject creation
│   │   │   ├── meetings.py       # CRUD for notes/transcripts, upload endpoints
│   │   │   └── ai.py             # Endpoints for semantic search, LLM extraction
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py         # Settings management (e.g., LLM key, DB connection strings)
│   │   ├── llm_service.py    # Wrapper for Gemini API calls (generation, embeddings)
│   │   ├── parser_service.py # Logic for reading, cleaning, and chunking content (PDF, HTML, TXT)
│   │   └── graph_service.py  # Logic for building/querying subject relationships (optional: a graph DB or simple relational structure)
│   ├── db/
│   │   ├── database.py       # Setup for SQL/NoSQL DB connection (e.g., SQLAlchemy engine)
│   │   ├── crud.py           # Functions for interacting with the structured DB
│   │   ├── models.py         # ORM models (e.g., Todo, Reference, Subject, History)
│   │   └── vector_store.py   # Client/utilities for Vector DB (e.g., ChromaDB client setup)
│   ├── schemas/              # Pydantic models for request/response validation
│   │   ├── todo.py
│   │   ├── knowledge.py
│   │   └── ai.py
│   └── exceptions/           # Custom exception handling
├── project.toml              # Python dependencies managed with uv (fastapi, uvicorn, pydantic, db-driver, llama-index/langchain, etc.)
├── Dockerfile                # For containerizing the backend
└── tests/
    ├── test_api.py
    └── test_core.py
```

## Key Integration Points

1. Content Ingestion (meetings.py, knowledge.py):

    * Action: User uploads a file (note/reference) or submits a URL.
    * Flow: The endpoint calls core.parser_service to read and chunk the content, then calls db.vector_store to generate embeddings via core.llm_service and index the chunks.
1. Content Ingestion: 
    * Action: When tool starts, the content folder may be parsed to see new or updated content for reindexing and refresh metadata.

1. Semantic Search (ai.py):
    * Action: User enters a query into the KnowledgeBase search bar.
    * Flow: The endpoint calls core.llm_service to generate an embedding for the query, uses db.vector_store to retrieve relevant knowledge chunks, and then uses RAG (Retrieval-Augmented Generation) via core.llm_service to generate a grounded answer.

1. Todo Extraction (ai.py):
    * Action: User clicks "Extract Todos" on a meeting note.
    * Flow: The endpoint sends the note/transcript content to core.llm_service with a system instruction to output a JSON list of action items. The backend then saves these new Todos via db.crud.

## Packaging

Both frontend and backend are docker images, can be started locally with docker-compose. 