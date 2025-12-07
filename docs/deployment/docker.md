# Docker Deployment

Complete guide for deploying MyAIAssistant using Docker.

## Docker Compose

### Production Deployment

```bash
# Build and start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Development with Hot Reload

```bash
# Start with development configuration
docker-compose -f docker-compose.dev.yml up

# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

Development mode features:

- Backend hot reload on code changes
- Frontend hot reload with Vite dev server
- Volume mounts for live development

## Separate Containers

### Backend Only

```bash
cd backend
docker build -t myaiassistant-backend .
docker run -p 8000:8000 myaiassistant-backend
```

With environment variables:

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./myaiassistant.db \
  myaiassistant-backend
```

With persistent data:

```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  myaiassistant-backend
```

### Frontend Only

```bash
cd frontend
docker build -t myaiassistant-frontend .
docker run -p 80:80 myaiassistant-frontend
```

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

volumes:
  backend-data:
```

### Development (`docker-compose.dev.yml`)

```yaml
services:
  backend:
    build: ./backend
    command: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    command: npm run dev -- --host 0.0.0.0
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
```

## Custom Ports

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Use port 8001 instead of 8000

  frontend:
    ports:
      - "8080:80"    # Use port 8080 instead of 80
```

## Data Persistence

### SQLite Database

The database is stored in the container. For persistence:

**Named volume (recommended):**

```yaml
volumes:
  - backend-data:/app/data
```

**Bind mount:**

```yaml
volumes:
  - ./backend/data:/app/data
```

### Backup and Restore

```bash
# Backup SQLite database
docker-compose exec backend cp /app/myaiassistant.db /app/data/backup.db

# Restore from backup
docker-compose exec backend cp /app/data/backup.db /app/myaiassistant.db
```

Volume backup:

```bash
# Create backup
docker run --rm -v myaiassistant_backend-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz /data

# Restore backup
docker run --rm -v myaiassistant_backend-data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/backup.tar.gz --strip 1"
```

## Health Checks

Add health checks to `docker-compose.yml`:

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

Check status:

```bash
# Check container status
docker-compose ps

# View resource usage
docker stats

# View logs
docker-compose logs backend
```

## Resource Limits

Set resource limits for production:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Network Configuration

### Custom Network

```yaml
networks:
  myaiassistant-network:
    driver: bridge

services:
  backend:
    networks:
      - myaiassistant-network

  frontend:
    networks:
      - myaiassistant-network
```

### Container Communication

- Frontend can access backend at `http://backend:8000`
- Backend accessible from host at `http://localhost:8000`

## Logging

Configure logging:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Check individual service
docker-compose logs backend
docker-compose logs frontend
```

### Port conflicts

```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :80

# Kill the process or change ports in docker-compose.yml
```

### Database issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Dependencies not updating

```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Complete cleanup
docker system prune -a --volumes
```

## Quick Reference

```bash
# Start production
docker-compose up -d

# Start development
docker-compose -f docker-compose.dev.yml up

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up -d --build

# Check status
docker-compose ps

# Scale service
docker-compose up -d --scale backend=3

# Execute command in container
docker-compose exec backend <command>

# View resource usage
docker stats
```

