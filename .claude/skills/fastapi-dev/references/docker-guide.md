# Docker and Deployment Guide for FastAPI

Production-ready Docker configuration and deployment patterns.

## Dockerfile - Multi-Stage Build

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser app ./app

# Set environment
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run application
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

## .dockerignore

```
__pycache__
*.pyc
*.pyo
*.egg-info/
.git
.gitignore
.env
.env.local
.venv
venv
.pytest_cache
.coverage
htmlcov
dist
build
*.db
.DS_Store
README.md
```

## docker-compose.yml

```yaml
version: "3.9"

services:
  fastapi:
    build: .
    container_name: fastapi-app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/fastapi_db
      - DEBUG=false
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: postgres-db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=fastapi_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

## Environment Configuration

### .env.example

```env
# Application
APP_NAME=FastAPI Application
DEBUG=false
SECRET_KEY=your-secret-key-here-change-in-production

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/fastapi_db

# API Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
CORS_CREDENTIALS=true
CORS_METHODS=["GET", "POST", "PUT", "DELETE"]
CORS_HEADERS=["*"]

# Security
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Logging
LOG_LEVEL=INFO
```

### config.py with Environment Support

```python
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application
    app_name: str = "FastAPI Application"
    debug: bool = False
    secret_key: str

    # Database
    database_url: str
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # CORS
    cors_origins: List[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
```

## Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f fastapi

# Execute command in container
docker-compose exec fastapi bash

# Rebuild without cache
docker-compose build --no-cache

# Remove everything (including volumes)
docker-compose down -v

# Run migrations in container
docker-compose exec fastapi alembic upgrade head

# Create database backup
docker-compose exec postgres pg_dump -U postgres fastapi_db > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres fastapi_db < backup.sql
```

## Deployment Patterns

### AWS ECS

```json
{
  "family": "fastapi-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "fastapi",
      "image": "your-registry/fastapi-app:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DEBUG",
          "value": "false"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:db-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fastapi",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Docker Hub Setup

```bash
# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 -t your-username/fastapi-app:latest --push .

# Tag for Docker Hub
docker tag fastapi-app:latest your-username/fastapi-app:v1.0

# Push to Docker Hub
docker push your-username/fastapi-app:v1.0
```

### Railway Deployment

```yaml
# railway.json
{
  "variables": {
    "DATABASE_URL": {
      "hidden": true,
      "description": "PostgreSQL connection string"
    },
    "SECRET_KEY": {
      "hidden": true,
      "description": "Application secret key"
    }
  },
  "build": {
    "builder": "dockerfile"
  }
}
```

```bash
# Deploy to Railway
railway up

# View logs
railway logs

# Set environment variables
railway variables set DEBUG=false
```

### Render Deployment

```yaml
# render.yaml
services:
  - type: web
    name: fastapi-app
    env: python
    plan: free
    branch: main
    buildCommand: pip install -r requirements.txt
    startCommand: fastapi run app/main.py --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: SECRET_KEY
        sync: false
      - key: DEBUG
        value: "false"
  - type: pserv
    name: postgres
    env: postgres
    plan: free
    ipAllowList: []
```

## Production Best Practices

1. **Use Multi-Stage Builds**
   - Reduces final image size
   - Separates build and runtime dependencies

2. **Run as Non-Root User**
   - Security best practice
   - Prevents container escape vulnerabilities

3. **Health Checks**
   - Enables automatic restart detection
   - Critical for orchestration platforms

4. **Environment Variables**
   - Never hardcode secrets
   - Use Docker secrets or environment variable services
   - Separate development and production configs

5. **Proper Signal Handling**
   - FastAPI/Uvicorn handles SIGTERM for graceful shutdown
   - Gives in-flight requests time to complete

6. **Resource Limits**
   ```yaml
   resources:
     limits:
       cpus: '1'
       memory: 512M
     reservations:
       cpus: '0.5'
       memory: 256M
   ```

7. **Logging**
   - Use structured logging
   - Forward to centralized service (CloudWatch, DataDog)
   - Monitor application metrics

8. **Database Migrations**
   ```dockerfile
   # Run before app starts
   RUN alembic upgrade head
   ```

## Troubleshooting

### Container Exit Immediately
```bash
# Check logs
docker-compose logs fastapi

# Common causes:
# - Missing environment variables
# - Database connection failure
# - Import errors in app
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Database Connection Timeout
```bash
# Ensure postgres service is running
docker-compose ps

# Check health
docker-compose exec postgres pg_isready

# Verify DATABASE_URL format
echo $DATABASE_URL
```

### Permission Denied Errors
```bash
# Ensure file ownership
docker-compose exec fastapi chown -R appuser:appuser /app

# Or rebuild with correct ownership in Dockerfile
```
