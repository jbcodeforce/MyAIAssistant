# Docker Deployment Guide

This guide covers Docker deployment options for the MyAIAssistant backend.

## Dockerfile Overview

The backend Dockerfile uses a multi-stage approach optimized for FastAPI applications:

- Base image: `python:3.12-slim`
- Package manager: `uv` (fast Python package installer)
- Dependencies: Installed from `pyproject.toml` and `uv.lock`
- Port: 8000
- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## Building the Backend Image

### Build the Docker image:

```bash
cd backend
docker build -t myaiassistant-backend .
```

### Run the container:

```bash
docker run -p 8000:8000 myaiassistant-backend
```

The API will be available at `http://localhost:8000`.

### With environment variables:

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./myaiassistant.db \
  myaiassistant-backend
```

### With volume mount for persistent data:

```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  myaiassistant-backend
```

## Using Docker Compose

### Production Deployment

Run both frontend and backend with production configuration:

```bash
docker-compose up -d
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:80`
- API Docs: `http://localhost:8000/docs`

### Stop services:

```bash
docker-compose down
```

### View logs:

```bash
docker-compose logs -f
```

### Rebuild after code changes:

```bash
docker-compose up -d --build
```

## Development with Docker Compose

For development with hot reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

Features:
- Backend hot reload on code changes
- Frontend hot reload with Vite dev server
- Volume mounts for live development
- Frontend on port 3000, backend on port 8000

## Docker Compose Configuration

### Production (`docker-compose.yml`)

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./myaiassistant.db
    volumes:
      - backend-data:/app/data
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### Development (`docker-compose.dev.yml`)

```yaml
services:
  backend:
    command: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
      
  frontend:
    command: npm run dev -- --host 0.0.0.0
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
```

## Environment Variables

Configure the backend using environment variables:

```bash
DATABASE_URL=sqlite:///./myaiassistant.db
```

### Setting environment variables:

#### Using docker run:

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./myaiassistant.db \
  myaiassistant-backend
```

#### Using .env file with docker-compose:

Create `.env` file in the project root:

```env
DATABASE_URL=sqlite:///./myaiassistant.db
```

Then run:

```bash
docker-compose up
```

## Data Persistence

### SQLite Database

The SQLite database is stored in the container. For persistence:

#### Option 1: Named volume (recommended)

```yaml
volumes:
  - backend-data:/app/data
```

#### Option 2: Bind mount

```yaml
volumes:
  - ./backend/data:/app/data
```

## Health Checks

Check if the backend is running:

```bash
curl http://localhost:8000/docs
```

Check container status:

```bash
docker-compose ps
```

View container logs:

```bash
docker-compose logs backend
```

## Troubleshooting

### Container won't start

Check logs:

```bash
docker-compose logs backend
```

### Port already in use

Change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Use port 8001 instead
```

### Database errors

Remove the volume and restart:

```bash
docker-compose down -v
docker-compose up
```

### Dependencies not updating

Rebuild the image:

```bash
docker-compose build --no-cache backend
docker-compose up
```

## Production Considerations

### 1. Use environment variables for secrets

Never hardcode secrets in the Dockerfile or docker-compose.yml.

### 2. Set resource limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### 3. Use health checks

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 4. Set restart policy

```yaml
services:
  backend:
    restart: unless-stopped
```

### 5. Use secrets management

For production, use Docker secrets or external secret management:

```yaml
services:
  backend:
    secrets:
      - db_password
```

## Multi-Stage Build Optimization

The Dockerfile uses a slim Python image to minimize size:

```dockerfile
FROM python:3.12-slim  # ~50MB smaller than full image
```

## Build Arguments

Customize the build with build arguments:

```bash
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  -t myaiassistant-backend .
```

## Network Configuration

### Custom network

```yaml
networks:
  myaiassistant-network:
    driver: bridge

services:
  backend:
    networks:
      - myaiassistant-network
```

### Access from host

Backend is accessible at `http://localhost:8000`

### Access from frontend container

Frontend can access backend at `http://backend:8000`

## Cleanup

### Remove all containers:

```bash
docker-compose down
```

### Remove volumes:

```bash
docker-compose down -v
```

### Remove images:

```bash
docker rmi myaiassistant-backend
docker rmi myaiassistant-frontend
```

### Complete cleanup:

```bash
docker-compose down -v --rmi all
```

## CI/CD Integration

### GitHub Actions example:

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t myaiassistant-backend ./backend
      - name: Push to registry
        run: docker push myaiassistant-backend
```

## Performance Optimization

1. Use `.dockerignore` to exclude unnecessary files
2. Order Dockerfile commands by frequency of change
3. Use multi-stage builds for smaller images
4. Leverage build cache with `--cache-from`
5. Use specific base image tags (not `latest`)

## Security Best Practices

1. Don't run as root user
2. Scan images for vulnerabilities
3. Use minimal base images
4. Keep base images updated
5. Use secrets management
6. Enable read-only root filesystem where possible

## Quick Reference

```bash
# Build
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Development mode
docker-compose -f docker-compose.dev.yml up

# Clean everything
docker-compose down -v --rmi all
```

