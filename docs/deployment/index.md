# Deployment Overview

MyAIAssistant can be deployed using Docker, locally for development, or on various cloud platforms.

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

