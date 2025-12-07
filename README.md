# [MyAIAssistant: Intelligent Todo and Knowledge Management](https://jbcodeforce.github.io/MyAIAssistant)

An intelligent personal productivity and knowledge management tool that integrates task management with a semantic knowledge base.

## Quick Start

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Access points:
# - Frontend: http://localhost:80
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

For local development:

```bash
# Backend
cd backend && uv sync && uv run uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Documentation

Full documentation available at [https://jeromeboyer.net/myaiassistant](https://jeromeboyer.net/myaiassistant) or run locally:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

## Key Features

| Feature | Status | Description |
| ------- | ------ | ----------- |
| Todo Management | Complete | Eisenhower Matrix (Urgent/Important) classification |
| Knowledge Base | Complete | Document and website reference storage |
| Semantic Search | Complete | RAG-powered search using ChromaDB |
| Task Linking | Planned | Automatic knowledge-to-task linking |
| LLM Chat | Planned | Action item extraction from meeting notes |

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
