# [MyAIAssistant: Intelligent Todo and Knowledge Management](https://jbcodeforce.github.io/MyAIAssistant)

An intelligent personal productivity and knowledge management tool that integrates task management with a semantic knowledge base using local LLM.

## Quick Start

* Clone this project:
    ```sh
    git clone https://github.com/jbcodeforce/MyAIAssistant.git
    ```

* If you have docker and docker compose:
    ```bash
    # Using Docker Compose (recommended)
    docker-compose up -d
    # User interface - Web Application main pages: http://localhost:80
    ```

* If you are on Mac, use the new `container` CLI

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
