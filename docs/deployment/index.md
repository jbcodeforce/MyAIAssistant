# Deployment Overview

MyAIAssistant can be deployed using Docker, locally for development, or on various cloud platforms.

## Quick Start

### Docker Compose (Recommended)

The fastest way to run the full application:

```bash
docker-compose up -d
```

Access points:

| Service | URL | Description |
| ------- | --- | ----------- |
| Frontend | http://localhost:80 | Vue.js application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |

### Local Development

For development with hot reload:

=== "Backend"

    ```bash
    cd backend
    uv sync
    uv run uvicorn app.main:app --reload
    ```

=== "Frontend"

    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Deployment Options

| Option | Use Case | Complexity |
| ------ | -------- | ---------- |
| [Docker Compose](docker.md) | Production, single server | Low |
| [Docker Containers](docker.md#separate-containers) | Microservices | Medium |
| [Local Development](configuration.md#local-development) | Development | Low |
| [Cloud Platforms](cloud.md) | Scalable production | High |

## Prerequisites

### For Docker Deployment

- Docker 20.10 or higher
- Docker Compose 2.0 or higher
- Ports 80 and 8000 available

### For Local Development

- Python 3.12+
- Node.js 18+
- uv package manager (recommended)

## Architecture

```
                    ┌──────────────────┐
                    │    Nginx/CDN     │
                    │   (Port 80/443)  │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌──────────────────┐          ┌──────────────────┐
    │     Frontend     │          │     Backend      │
    │   (Vue.js/Nginx) │   ──▶    │    (FastAPI)     │
    │     Port 80      │  /api    │    Port 8000     │
    └──────────────────┘          └────────┬─────────┘
                                           │
                              ┌────────────┴────────────┐
                              │                         │
                              ▼                         ▼
                    ┌──────────────────┐      ┌──────────────────┐
                    │     SQLite       │      │    ChromaDB      │
                    │  (Relational)    │      │   (Vectors)      │
                    └──────────────────┘      └──────────────────┘
```

## Data Persistence

Two storage systems require persistence:

1. **SQLite Database**: Todos and knowledge metadata
2. **ChromaDB**: Vector embeddings for search

Docker volumes handle this automatically:

```yaml
volumes:
  - backend-data:/app/data          # ChromaDB vectors
  - ./myaiassistant.db:/app/myaiassistant.db  # SQLite
```

## Health Monitoring

Check application health:

```bash
# Backend health
curl http://localhost:8000/health

# Container status
docker-compose ps

# View logs
docker-compose logs -f
```

## Next Steps

- [Docker Deployment Guide](docker.md) - Detailed Docker configuration
- [Cloud Deployment](cloud.md) - Deploy to AWS, GCP, Azure
- [Configuration Reference](configuration.md) - Environment variables and settings

