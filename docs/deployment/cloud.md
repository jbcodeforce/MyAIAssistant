# Cloud Deployment

Deploy MyAIAssistant to various cloud platforms.

## AWS (Amazon Web Services)

### EC2 (Virtual Server)

1. Launch an EC2 instance (Ubuntu 22.04 recommended)
2. Install Docker and Docker Compose:

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
```

3. Clone and deploy:

```bash
git clone <repository-url>
cd MyAIAssistant
docker-compose up -d
```

4. Configure security groups:
   - Allow inbound TCP 80 (HTTP)
   - Allow inbound TCP 8000 (API)
   - Allow inbound TCP 443 (HTTPS) if using SSL

### ECS (Elastic Container Service)

1. Push images to Amazon ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag myaiassistant-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/myaiassistant-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/myaiassistant-backend:latest
```

2. Create ECS task definitions
3. Create ECS service with load balancer
4. Configure target groups for health checks

## Google Cloud Platform

### Compute Engine

1. Create a VM instance
2. Install Docker:

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
```

3. Deploy with docker-compose

### Cloud Run

Deploy as serverless containers:

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/myaiassistant-backend ./backend
gcloud builds submit --tag gcr.io/PROJECT_ID/myaiassistant-frontend ./frontend

# Deploy to Cloud Run
gcloud run deploy myaiassistant-backend \
  --image gcr.io/PROJECT_ID/myaiassistant-backend \
  --platform managed \
  --allow-unauthenticated
```

## Microsoft Azure

### Container Instances

1. Create Azure Container Registry
2. Push images:

```bash
az acr login --name myregistry
docker tag myaiassistant-backend myregistry.azurecr.io/myaiassistant-backend
docker push myregistry.azurecr.io/myaiassistant-backend
```

3. Create container group:

```bash
az container create \
  --resource-group mygroup \
  --name myaiassistant \
  --image myregistry.azurecr.io/myaiassistant-backend \
  --ports 8000
```

## DigitalOcean

### Droplets

1. Create a Docker Droplet from marketplace
2. SSH and deploy:

```bash
git clone <repository-url>
cd MyAIAssistant
docker-compose up -d
```

### App Platform

1. Connect GitHub repository
2. Configure build settings:
   - Backend: Dockerfile in `./backend`
   - Frontend: Dockerfile in `./frontend`
3. Set environment variables
4. Deploy

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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Traefik

Add labels to `docker-compose.yml`:

```yaml
services:
  backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=Host(`yourdomain.com`) && PathPrefix(`/api`)"
      - "traefik.http.services.backend.loadbalancer.server.port=8000"

  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`yourdomain.com`)"
      - "traefik.http.services.frontend.loadbalancer.server.port=80"
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Generate certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

### Docker with Let's Encrypt

Add certbot service:

```yaml
services:
  certbot:
    image: certbot/certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

## Scaling

### Horizontal Scaling

Scale backend instances:

```yaml
services:
  backend:
    deploy:
      replicas: 3
```

Or via command:

```bash
docker-compose up -d --scale backend=3
```

### Load Balancer

Add nginx load balancer:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
```

### Database Considerations

For production scaling:

- Replace SQLite with PostgreSQL
- Use managed database service (RDS, Cloud SQL)
- Configure connection pooling
- Set up read replicas for high traffic

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

The backend exposes a health endpoint:

```bash
curl http://localhost:8000/health
```

Consider adding:

- Prometheus metrics
- Grafana dashboards
- Log aggregation (ELK, CloudWatch)

## Security Checklist

- [ ] Use environment variables for secrets
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Use network isolation
- [ ] Keep base images updated
- [ ] Implement rate limiting
- [ ] Use strong passwords
- [ ] Enable container security scanning
- [ ] Restrict container capabilities
- [ ] Use non-root users in containers

