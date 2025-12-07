# MyAIAssistant Deployment Guide

This guide covers deployment options for the MyAIAssistant full-stack application.

## Quick Start with Docker Compose

The fastest way to get the entire application running:

```bash
docker-compose up -d
```

Access the application:
- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Deployment Options

### 1. Docker Compose (Recommended)

#### Production Deployment

```bash
# Build and start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Development with Hot Reload

```bash
# Start with development configuration
docker-compose -f docker-compose.dev.yml up

# Frontend available at http://localhost:3000
# Backend available at http://localhost:8000
```

### 2. Separate Docker Containers

#### Backend Only

```bash
cd backend
docker build -t myaiassistant-backend .
docker run -p 8000:8000 myaiassistant-backend
```

#### Frontend Only

```bash
cd frontend
docker build -t myaiassistant-frontend .
docker run -p 80:80 myaiassistant-frontend
```

### 3. Local Development (No Docker)

#### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Configuration

### Backend Environment Variables

Create `.env` file in the project root:

```env
DATABASE_URL=sqlite:///./myaiassistant.db
```

### Frontend Configuration

The frontend proxies API requests to the backend. Configure in `frontend/vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## Production Deployment

### Prerequisites

- Docker and Docker Compose installed
- Ports 80 and 8000 available

### Steps

1. Clone the repository:

```bash
git clone <repository-url>
cd MyAIAssistant
```

2. Build and start services:

```bash
docker-compose up -d --build
```

3. Verify deployment:

```bash
# Check services are running
docker-compose ps

# View logs
docker-compose logs -f

# Test backend
curl http://localhost:8000/docs

# Test frontend
curl http://localhost:80
```

4. Access the application:

Open http://localhost in your browser.

### Using Custom Ports

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

## Cloud Deployment

### AWS (Amazon Web Services)

#### Using EC2

1. Launch an EC2 instance (Ubuntu 22.04)
2. Install Docker and Docker Compose
3. Clone the repository
4. Run `docker-compose up -d`
5. Configure security groups to allow ports 80 and 8000

#### Using ECS (Elastic Container Service)

1. Push images to ECR
2. Create task definitions
3. Create ECS service
4. Configure load balancer

### Google Cloud Platform

#### Using Compute Engine

1. Create a VM instance
2. Install Docker and Docker Compose
3. Deploy with docker-compose

#### Using Cloud Run

1. Build and push images to Google Container Registry
2. Deploy each service to Cloud Run
3. Configure internal networking

### Azure

#### Using Azure Container Instances

1. Push images to Azure Container Registry
2. Create container groups
3. Configure networking

### DigitalOcean

#### Using Droplets

1. Create a Docker Droplet
2. Clone repository
3. Run docker-compose

#### Using App Platform

1. Push to GitHub
2. Connect repository to App Platform
3. Configure build and deploy settings

## Reverse Proxy Setup

### Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Traefik

```yaml
services:
  backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`yourdomain.com`) && PathPrefix(`/api`)"
      
  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`yourdomain.com`)"
```

## SSL/TLS Configuration

### Using Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Docker with Let's Encrypt

Add certbot service to `docker-compose.yml`:

```yaml
services:
  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
```

## Scaling

### Horizontal Scaling

#### Backend

```yaml
services:
  backend:
    deploy:
      replicas: 3
```

#### Load Balancer

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - backend
```

### Database Scaling

For production, consider:
- PostgreSQL instead of SQLite
- Database replication
- Connection pooling

## Monitoring

### Container Health

```bash
# Check container status
docker-compose ps

# View resource usage
docker stats

# View logs
docker-compose logs -f
```

### Application Monitoring

Add health check endpoints:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Logging

Centralized logging with ELK stack or cloud services:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Backup and Recovery

### Database Backup

```bash
# Backup SQLite database
docker-compose exec backend cp /app/myaiassistant.db /app/data/backup.db

# Restore from backup
docker-compose exec backend cp /app/data/backup.db /app/myaiassistant.db
```

### Volume Backup

```bash
# Create backup
docker run --rm -v myaiassistant_backend-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/backup.tar.gz /data

# Restore backup
docker run --rm -v myaiassistant_backend-data:/data -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/backup.tar.gz --strip 1"
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

# Kill the process or change ports
```

### Database issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### Build failures

```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Performance Optimization

### Docker

1. Use multi-stage builds
2. Minimize layers
3. Use `.dockerignore`
4. Leverage build cache
5. Use specific image tags

### Application

1. Enable gzip compression
2. Cache static assets
3. Use CDN for frontend
4. Optimize database queries
5. Add Redis for caching

## Security Checklist

- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Use network isolation
- [ ] Regular security updates
- [ ] Implement rate limiting
- [ ] Use strong passwords
- [ ] Enable container security scanning
- [ ] Restrict container capabilities
- [ ] Use non-root users in containers

## Maintenance

### Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Remove old images
docker image prune -a
```

### Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service
docker-compose logs backend
```

### Cleanup

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

## Support

For detailed documentation:
- Backend: `backend/README.md`, `backend/DOCKER.md`
- Frontend: `frontend/README.md`, `frontend/QUICKSTART.md`
- Docker: `backend/DOCKER.md`

