# MyAIAssistant

An intelligent personal productivity and knowledge management tool that integrates task management with a semantic knowledge base, that should help user to work on tasks, with continous knowledge of previous meeting notes, tasks, technical local knowledge. It helps to build weekly report on metrics like:

* Number of customer meetings
* Customer roadblocks addressed
* Assets completed or started
* Task created, completed

## Project Goals

MyAIAssistant helps users organize tasks, reference subject-matter knowledge, and leverage AI for semantic search, note summarization, task extraction and recommandation. The tool links knowledge artifacts to tasks to provide better context when addressing work.

Based on Stephen Covey's "7 Habits of Highly Effective People," the system helps manage priorities efficiently using the Eisenhower Matrix (Urgent/Important classification).

![](./images/aia_dashboard.png)

With a drag-and-drop user interface it is easy to continuously re-prioritize tasks.

[Access the webApp local once started](http://localhost:3000).

## Core Features

| Feature | Status | Description |
| ------- | ------ | ----------- |
| Kanban-style Todo Management | Completed | Todos categorized by Importance/Urgency (Eisenhower Matrix) |
| Knowledge Base | Completed | Metadata storage referencing documents, notes, and website links |
| Semantic Search (RAG) | Completed | AI-powered search across the knowledge base using embeddings |
| LLM Chat Support | Completed | AI chat for task planning and knowledge base queries |
| Task/Note Integration | Planned | Automatic linking of Todos to relevant knowledge artifacts |

## Technical Stack

| Layer | Technology | Purpose |
| ----- | ---------- | ------- |
| Frontend | Vue.js with Vite | User interface with drag-and-drop Todo visualization |
| Backend API | Python FastAPI | Async API for logic and data orchestration |
| Relational Database | SQLite (PostgreSQL-ready) | Storing Todos, user settings, knowledge metadata |
| Vector Database | ChromaDB | Semantic search and RAG using text embeddings |
| LLM Integration | OpenAI SDK | Semantic search, summarization, task generation |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Vue.js Frontend                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Dashboard  │  │  Knowledge  │  │  Unclassified View  │  │
│  │  (Matrix)   │  │    View     │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Todo API   │  │ Knowledge   │  │      RAG API        │  │
│  │  /api/v1/   │  │    API      │  │  (Index & Search)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                     │                        │
                     ▼                        ▼
          ┌──────────────────┐    ┌──────────────────────┐
          │     SQLite       │    │      ChromaDB        │
          │  (Relational DB) │    │   (Vector Store)     │
          └──────────────────┘    └──────────────────────┘
```

## Quick Start

### Using Docker Compose

```bash
docker-compose up -d
```

Access points:

- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

* Set CONFIG_environment variables to support different persistence references:
    ```sh
    # For development and testing set the biz config which persist in workspace/biz-db
    export CONFIG_FILE=./tests/biz-config.yaml
    # Or for technical content development
    export CONFIG_FILE=./tests/km-config.yaml
    ```
* Backend:
    ```bash
    cd backend
    uv sync
    uv run uvicorn app.main:app --reload
    ```

* Frontend:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

* Tools:
    ```sh
    cd backend
    uv run tools/vectorize_folder.py
    ```

## Project Principles

1. **Run locally** - All core features work without external API dependencies
2. **External configuration** - Environment-based configuration for flexibility
3. **Privacy-first** - Data stays on local infrastructure
4. **Efficient prioritization** - Eisenhower Matrix helps focus on high-impact work

## Activities

# Create Knowledge base

Tool to vectorize folder content into ChromaDB for RAG.

This script scans a folder for supported documents (markdown, text, HTML),
processes them through the RAG pipeline, stores embeddings in ChromaDB,
and saves metadata to the knowledge base database.

The tool is reentrant: re-running it will update existing documents if their
content has changed, and skip unchanged files.

## Features

Code is: `backend/tools/vectorize_folder.py`

This CLI tool leverages the existing backend services:

* DocumentLoader for loading markdown and HTML files
* RecursiveTextSplitter for chunking content
* ChromaDB with all-MiniLM-L6-v2 embeddings


* Recursive folder scanning for supported file types
* Configurable chunk size and overlap
* Category and tags metadata support
* Progress logging with file-by-file status
* Collection statistics view
* Handles .md, .markdown, .txt, and .html files
