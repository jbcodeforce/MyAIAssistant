# [MyAIAssistant: Intelligent Todo and Knowledge Management](https://jbcodeforce.github.io/MyAIAssistant)

An intelligent personal productivity and knowledge management tool that integrates task management with a semantic knowledge base using LLM, GraphRAG.

[Read the documentation online](https://jbcodeforce.github.io/MyAIAssistan).

## Core Features

| Feature | Status | Description |
| ------- | ------ | ----------- |
| Kanban-style Todo Management | Completed | Todos categorized by Importance/Urgency (Eisenhower Matrix) |
| Organization Management | Completed | Track organizations with stakeholders, team, strategy |
| Project Management | Completed | Manage projects with status lifecycle (Draft, Active, On Hold, Completed, Cancelled) linked to organizations |
| Knowledge Base | Completed | Metadata storage referencing documents, notes, and website links |
| Semantic Search (RAG) | Completed | AI-powered search across the knowledge base using embeddings |
| LLM Chat Support | Completed | AI chat for task planning and knowledge base queries |
| Asset management | To list assets that you are developing and need recurring activities | 
| Task/Note Integration | Planned | Automatic linking of Todos to relevant knowledge artifacts |

## Quick Start

### Option 1: One-line Install (No Clone Required)

```bash
curl -fsSL https://raw.githubusercontent.com/jbcodeforce/MyAIAssistant/main/install.sh | bash
```

This script:
- Checks for Docker and offers to install it if missing
- Downloads `docker-compose.yml` and creates a default `config.yaml`
- Sets up the installation in `~/myaiassistant` (override with `MYAIASSISTANT_DIR`)

After installation:
```bash
cd ~/myaiassistant
docker compose up -d
# Web UI: http://localhost:80
```

### Option 2: Clone and Run

```sh
git clone https://github.com/jbcodeforce/MyAIAssistant.git
cd MyAIAssistant
docker compose up -d
# Web UI: http://localhost:80
```

### For local development

* Only during development run backend and frontend using `uv` and `npm`.
    ```bash
    # Backend
    cd backend && uv sync && uv run uvicorn app.main:app --reload

    # Frontend
    cd frontend && npm install && npm run dev

    # Access points:
    # - User interface - Web Application main pages: http://localhost:3000
    # - Backend API: http://localhost:8000
    # - API Docs: http://localhost:8000/docs
    ```

* Build docker images:
    ```sh
    ./build.sh           # builds with :latest tag
    # or
    ./build.sh v1.0.0    # builds with :v1.0.0 tag
    ```

## Documentation

Full documentation available at [https://jeromeboyer.net/myaiassistant](https://jeromeboyer.net/myaiassistant) or in the application itself.

## Technical Stack

| Layer | Technology |
| ----- | ---------- |
| Frontend | Vue.js 3 with Vite |
| Backend | Python FastAPI |
| Database | SQLite (PostgreSQL-ready) |
| Vector Store | ChromaDB |
| Embeddings | sentence-transformers (local) |

## Project Structure

```
MyAIAssistant/
├── backend/        # FastAPI application
├── frontend/       # Vue.js application
├── docs/           # MkDocs documentation
└── docker-compose.yml
```

## License

MIT 
