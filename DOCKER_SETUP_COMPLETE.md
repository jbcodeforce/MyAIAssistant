# Docker Setup Complete

Docker deployment for MyAIAssistant is now fully configured.

## Files Created/Updated

### Backend Docker Files

1. **`backend/Dockerfile`**
   - Multi-stage Python 3.12 build
   - Uses `uv` for fast dependency installation
   - Optimized for FastAPI applications
   - Exposes port 8000

2. **`backend/.dockerignore`**
   - Excludes unnecessary files from Docker build
   - Reduces image size and build time

3. **`backend/DOCKER.md`**
   - Comprehensive Docker deployment guide
   - Environment configuration
   - Troubleshooting tips
   - Production best practices

### Docker Compose Files

4. **`docker-compose.yml`** (Production)
   - Full-stack deployment
   - Backend on port 8000
   - Frontend on port 80
   - Persistent data volumes
   - Auto-restart policies

5. **`docker-compose.dev.yml`** (Development)
   - Hot reload for both services
   - Volume mounts for live development
   - Frontend dev server on port 3000

### Documentation

6. **`DEPLOYMENT.md`**
   - Complete deployment guide
   - Cloud deployment options (AWS, GCP, Azure, DigitalOcean)
   - SSL/TLS configuration
   - Scaling strategies
   - Security best practices
   - Monitoring and backup

7. **`backend/README.md`** (Updated)
   - Added Docker installation instructions
   - Links to Docker documentation

## Quick Start

### Production Deployment

Run the entire stack:

```bash
docker-compose up -d
```

Access:
- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Development Mode

With hot reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

### Backend Only

```bash
cd backend
docker build -t myaiassistant-backend .
docker run -p 8000:8000 myaiassistant-backend
```

## Docker Images

### Backend Image

**Base:** `python:3.12-slim`

**Features:**
- Fast dependency installation with `uv`
- Minimal image size
- Security-optimized
- Production-ready

**Build:**
```bash
cd backend
docker build -t myaiassistant-backend .
```

**Run:**
```bash
docker run -p 8000:8000 myaiassistant-backend
```

### Frontend Image

**Base:** `node:18-alpine` (build) + `nginx:alpine` (production)

**Features:**
- Multi-stage build for minimal size
- Nginx for static file serving
- Optimized for production
- API proxy configuration

**Build:**
```bash
cd frontend
docker build -t myaiassistant-frontend .
```

**Run:**
```bash
docker run -p 80:80 myaiassistant-frontend
```

## Docker Compose Services

### Production (`docker-compose.yml`)

```yaml
services:
  backend:
    - Port: 8000
    - Volume: backend-data
    - Restart: unless-stopped
    
  frontend:
    - Port: 80
    - Depends on: backend
    - Restart: unless-stopped
```

### Development (`docker-compose.dev.yml`)

```yaml
services:
  backend:
    - Port: 8000
    - Hot reload enabled
    - Volume mounted for live changes
    
  frontend:
    - Port: 3000
    - Vite dev server
    - Volume mounted for live changes
```

## Common Commands

### Start Services

```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up

# Rebuild and start
docker-compose up -d --build
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Complete cleanup
docker-compose down -v --rmi all
```

### Manage Services

```bash
# Check status
docker-compose ps

# Restart service
docker-compose restart backend

# Execute command
docker-compose exec backend bash

# View resource usage
docker stats
```

## Environment Variables

### Backend

Create `.env` file in project root:

```env
DATABASE_URL=sqlite:///./myaiassistant.db
```

### Docker Compose

Variables are automatically loaded from `.env` file:

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

## Data Persistence

### Volumes

The database is persisted using Docker volumes:

```yaml
volumes:
  backend-data:
```

### Backup

```bash
# Create backup
docker run --rm -v myaiassistant_backend-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz /data

# Restore backup
docker run --rm -v myaiassistant_backend-data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/backup.tar.gz --strip 1"
```

## Network Configuration

Services communicate over Docker network:

- Frontend → Backend: `http://backend:8000`
- External → Frontend: `http://localhost:80`
- External → Backend: `http://localhost:8000`

## Port Mapping

Default ports:

| Service  | Internal | External |
|----------|----------|----------|
| Backend  | 8000     | 8000     |
| Frontend | 80       | 80       |
| Frontend (dev) | 3000 | 3000 |

Change ports in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Use port 8001 instead
```

## Troubleshooting

### Services won't start

```bash
docker-compose logs
```

### Port already in use

```bash
# Check what's using the port
sudo lsof -i :8000
sudo lsof -i :80

# Change ports in docker-compose.yml
```

### Build failures

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Database issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

## Production Checklist

- [ ] Use environment variables for secrets
- [ ] Configure SSL/TLS certificates
- [ ] Set up reverse proxy (Nginx/Traefik)
- [ ] Enable CORS properly
- [ ] Configure resource limits
- [ ] Set up monitoring and logging
- [ ] Implement backup strategy
- [ ] Use container security scanning
- [ ] Configure health checks
- [ ] Set up CI/CD pipeline

## Cloud Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:

- AWS deployment (EC2, ECS, Fargate)
- Google Cloud Platform (Compute Engine, Cloud Run)
- Azure (Container Instances, App Service)
- DigitalOcean (Droplets, App Platform)
- Kubernetes deployment
- SSL/TLS configuration
- Scaling strategies

## Security Best Practices

1. **Don't run as root**
   - Use non-root users in containers
   
2. **Secrets management**
   - Use environment variables
   - Never commit secrets to git
   
3. **Network security**
   - Use internal networks
   - Expose only necessary ports
   
4. **Image security**
   - Use official base images
   - Regular security updates
   - Scan for vulnerabilities
   
5. **Container hardening**
   - Read-only root filesystem
   - Drop unnecessary capabilities
   - Use security profiles

## Performance Tips

1. **Image optimization**
   - Use `.dockerignore`
   - Multi-stage builds
   - Layer caching
   
2. **Resource management**
   - Set memory limits
   - Set CPU limits
   
3. **Network optimization**
   - Use internal network
   - Enable HTTP/2
   - Gzip compression

## Documentation

For more details, see:

- **Backend Docker**: `backend/DOCKER.md`
- **Deployment Guide**: `DEPLOYMENT.md`
- **Backend README**: `backend/README.md`
- **Frontend README**: `frontend/README.md`

## Support

For issues:

1. Check logs: `docker-compose logs`
2. Verify configuration
3. Review documentation
4. Check GitHub issues

## Next Steps

1. Test the deployment:
   ```bash
   docker-compose up -d
   ```

2. Access the application:
   - Frontend: http://localhost
   - API: http://localhost:8000/docs

3. Create your first todo

4. For production, review [DEPLOYMENT.md](DEPLOYMENT.md)

## Summary

The MyAIAssistant application is now fully containerized with:

- Production-ready Docker images
- Development environment with hot reload
- Docker Compose orchestration
- Comprehensive documentation
- Best practices implemented
- Cloud deployment guides

Simply run `docker-compose up -d` to get started!

