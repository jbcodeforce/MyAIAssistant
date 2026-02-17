# Knowledge Management Database

This workspace provides isolated PostgreSQL and ChromaDB storage for general knowledge management.

## Isolation Strategy

Each workspace maintains its own:

- **PostgreSQL database**: Uses a workspace-specific named volume (`km-postgres-data`)
- **ChromaDB vector store**: Stored locally in `./data/chroma/` directory
- **Configuration**: Workspace-specific `config.yaml`

## Quick Start

Development mode:

```sh
docker compose -f docker-compose.dev.yml up -d
```

Production mode:

```sh
docker compose up -d
```

## Port Mapping

| Service    | Container Port | Host Port |
|------------|----------------|-----------|
| PostgreSQL | 5432           | 5434      |
| Backend    | 8000           | 8001      |
| Frontend   | 3000/80        | 3001      |

These ports differ from `biz-db` to allow running both workspaces simultaneously.

## Database Access

```sh
docker exec -it km-db-postgres psql -U postgres -d km_assistant
```

## Volume Management

```sh
docker volume ls | grep km-postgres
```

