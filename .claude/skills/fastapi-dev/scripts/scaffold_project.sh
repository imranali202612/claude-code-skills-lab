#!/bin/bash
# Scaffold a new FastAPI project with professional structure

set -e

PROJECT_NAME="${1:-.}"
PYTHON_VERSION="${2:-3.11}"

echo "🚀 FastAPI Project Scaffolding"
echo "Project: $PROJECT_NAME"

# Create directory structure
mkdir -p "$PROJECT_NAME"/{app/{models,schemas,crud,routers},tests}

# Create __init__.py files
touch "$PROJECT_NAME/app/__init__.py"
touch "$PROJECT_NAME/app/models/__init__.py"
touch "$PROJECT_NAME/app/schemas/__init__.py"
touch "$PROJECT_NAME/app/crud/__init__.py"
touch "$PROJECT_NAME/app/routers/__init__.py"
touch "$PROJECT_NAME/tests/__init__.py"

# Create main configuration files
cat > "$PROJECT_NAME/app/config.py" << 'EOF'
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "FastAPI Application"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/fastapi_db"
    jwt_secret_key: str = "your-secret-key-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
EOF

cat > "$PROJECT_NAME/app/database.py" << 'EOF'
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
EOF

cat > "$PROJECT_NAME/app/main.py" << 'EOF'
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, init_db
from sqlmodel import SQLModel

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    await init_db()
    yield
    # Shutdown
    print("Shutting down...")
    await engine.dispose()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}
EOF

cat > "$PROJECT_NAME/app/dependencies.py" << 'EOF'
# Shared dependencies go here
EOF

cat > "$PROJECT_NAME/.env.example" << 'EOF'
# Application
APP_NAME=FastAPI Application
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/fastapi_db

# Security
JWT_SECRET_KEY=your-secret-key-here
EOF

cat > "$PROJECT_NAME/.env" << 'EOF'
# Application
APP_NAME=FastAPI Application
DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/fastapi_db

# Security
JWT_SECRET_KEY=dev-secret-key-change-in-production
EOF

cat > "$PROJECT_NAME/requirements.txt" << 'EOF'
fastapi==0.108.0
uvicorn[standard]==0.24.0
sqlmodel==0.0.14
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
psycopg[asyncio]==3.1.13
pydantic-settings==2.1.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
EOF

cat > "$PROJECT_NAME/requirements-dev.txt" << 'EOF'
-r requirements.txt
black==23.12.0
flake8==6.1.0
mypy==1.7.1
isort==5.13.2
EOF

cat > "$PROJECT_NAME/Dockerfile" << 'EOF'
FROM python:3.11-slim as builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client && rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 1000 appuser

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser app ./app

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
EOF

cat > "$PROJECT_NAME/docker-compose.yml" << 'EOF'
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
EOF

cat > "$PROJECT_NAME/.dockerignore" << 'EOF'
__pycache__
*.pyc
*.egg-info/
.git
.env
.venv
venv
.pytest_cache
*.db
EOF

cat > "$PROJECT_NAME/tests/conftest.py" << 'EOF'
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.main import app
from app.database import get_session

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
def client(test_session):
    def override_get_session():
        return test_session
    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()
EOF

cat > "$PROJECT_NAME/README.md" << 'EOF'
# FastAPI Application

Professional FastAPI project with PostgreSQL, async support, and Docker.

## Getting Started

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create .env from .env.example:
```bash
cp .env.example .env
```

3. Start database (Docker):
```bash
docker-compose up -d postgres
```

4. Run application:
```bash
fastapi dev app/main.py
```

5. View API docs: http://localhost:8000/docs

### With Docker

```bash
docker-compose up -d
```

Application available at http://localhost:8000

### Testing

```bash
pytest
pytest -v  # Verbose
pytest --cov=app  # Coverage
```

## Project Structure

```
app/
├── main.py           # FastAPI app setup
├── config.py         # Settings and environment
├── database.py       # Database connection
├── dependencies.py   # Shared dependencies
├── models/          # SQLModel definitions
├── schemas/         # Pydantic schemas
├── crud/            # Database operations
└── routers/         # API endpoints
```

## Database

PostgreSQL via Docker. Connection managed through async SQLAlchemy.

Migration management: Use Alembic for production.

## Development

- Python 3.11+
- FastAPI 0.108+
- PostgreSQL 16+
- Async/await throughout

See references in `.claude/skills/fastapi-dev/` for detailed patterns.
EOF

echo "✅ Project created at: $PROJECT_NAME"
echo "📦 Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. cp .env.example .env"
echo "  3. pip install -r requirements.txt"
echo "  4. docker-compose up -d postgres"
echo "  5. fastapi dev app/main.py"
echo ""
echo "📖 View API docs at http://localhost:8000/docs"
