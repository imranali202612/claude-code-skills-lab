---
name: fastapi-dev
description: |
  Automate FastAPI project development from hello world through production-ready APIs.
  Use when building REST APIs with endpoint scaffolding, database integration, testing, and Docker deployment workflows.
allowed-tools: Read, Glob, Bash, Write, Edit
---

# FastAPI Development Automation

This skill automates FastAPI project development workflows, guiding you from basic endpoints to production-ready applications with PostgreSQL databases, comprehensive testing, and deployment.

## How This Skill Works

```
User: "Set up a FastAPI project for a todo API"
       ↓
Skill gathers context (project name, database choice, features needed)
       ↓
Skill scaffolds project structure with best practices
       ↓
Skill generates endpoints, models, tests, and Docker setup
       ↓
Production-ready project with embedded domain patterns
```

## When to Invoke

This skill should be used when you need to:
- Initialize a new FastAPI project with professional structure
- Add database integration with SQLAlchemy/SQLModel
- Create CRUD endpoints with validation and error handling
- Set up testing infrastructure
- Configure Docker and deployment workflows
- Understand FastAPI best practices through generated code

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing FastAPI projects, project structure conventions |
| **Conversation** | Project name, API domain (users, todos, products), desired features |
| **Skill References** | FastAPI patterns, SQLModel integration, async best practices, Docker templates |
| **User Guidelines** | Team conventions, specific tech preferences, deployment targets |

Ensure all required context is gathered before scaffolding.

---

## Clarification Questions

Ask user for these project-specific details:

### 1. Project Scope

- **Project name and description** - What is this API for?
- **Primary domain/entities** - What are main data models? (users, todos, products, etc.)
- **Endpoints needed** - Which CRUD operations? Just basic or advanced features?

### 2. Database Configuration

- **Database choice** - PostgreSQL (default), SQLite, or other?
- **Database location** - Local development, Neon (managed), self-hosted?
- **Authentication needed** - JWT, OAuth2, basic, or none?

### 3. Development Environment

- **Python version** - 3.10+ (recommended) or 3.9?
- **Async patterns** - Full async (async/await), or mixed sync/async?
- **Additional libraries** - Alembic migrations, Celery tasks, logging, etc.?

### 4. Deployment Target

- **Deployment environment** - Docker/local, cloud (AWS/GCP/Azure), containerized?
- **Environment management** - .env files, secret management approach?

---

## Core Workflows

### Workflow 1: Project Scaffolding

**Goal**: Create professional project structure with all necessary files.

**Steps**:
1. Create project directory with standard structure:
   ```
   project-name/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py          # FastAPI app instance
   │   ├── config.py        # Settings and environment config
   │   ├── database.py      # Database setup
   │   ├── models/          # SQLModel definitions
   │   ├── schemas/         # Pydantic request/response models
   │   ├── crud/            # Database operations
   │   ├── routers/         # Endpoint groups
   │   └── dependencies.py  # Shared dependencies
   ├── tests/               # Test suite
   ├── requirements.txt     # Python dependencies
   ├── .env.example         # Environment template
   ├── Dockerfile           # Container config
   ├── docker-compose.yml   # Multi-container setup
   └── README.md            # Project documentation
   ```

2. Install dependencies (fastapi, uvicorn, sqlmodel, psycopg[asyncio], python-dotenv, pytest)

3. Generate base files with embedded best practices:
   - `main.py` with lifespan events, exception handlers
   - `database.py` with async session management
   - `config.py` with environment variable handling
   - `.env.example` template
   - `Dockerfile` for production deployment
   - `docker-compose.yml` for PostgreSQL integration

### Workflow 2: Model and Schema Generation

**Goal**: Create data models and validation schemas following FastAPI conventions.

**Steps**:
1. Create SQLModel base class in `models/__init__.py` with common fields (id, created_at, updated_at)
2. Generate entity-specific models:
   - Base model (shared fields)
   - Database model (with table=True)
   - Create schema (input validation)
   - Update schema (partial updates)
   - Response schema (public view)
3. Add proper field validation (required vs optional, constraints)
4. Generate corresponding Pydantic schemas in `schemas/`

### Workflow 3: CRUD and Route Generation

**Goal**: Create endpoints with proper error handling and validation.

**Steps**:
1. Generate CRUD functions in `crud/` following repository pattern:
   - `create(db_session, obj_in)` - INSERT with validation
   - `read(db_session, id)` - SELECT by ID
   - `read_all(db_session, skip, limit)` - SELECT with pagination
   - `update(db_session, id, obj_in)` - UPDATE with partial support
   - `delete(db_session, id)` - DELETE
2. Create router in `routers/` with:
   - GET /items/ (list with pagination)
   - GET /items/{id} (single item with 404 handling)
   - POST /items/ (create with 409 conflict handling)
   - PUT /items/{id} (full update)
   - PATCH /items/{id} (partial update)
   - DELETE /items/{id} (soft or hard delete)
3. Include proper HTTP status codes (200, 201, 204, 400, 404, 409, 500)
4. Add dependency injection for database sessions

### Workflow 4: Testing Infrastructure

**Goal**: Set up comprehensive testing with pytest and TestClient.

**Steps**:
1. Create `tests/conftest.py` with:
   - Test database connection
   - TestClient setup
   - Dependency overrides
   - Fixtures for common test data
2. Generate test files for each router:
   - Test successful operations (201, 200, 204)
   - Test validation errors (400)
   - Test authentication/authorization (401, 403)
   - Test not found errors (404)
   - Test conflict errors (409)
3. Add async test support for database operations

### Workflow 5: Docker and Deployment

**Goal**: Create production-ready Docker configuration.

**Steps**:
1. Generate `Dockerfile` with:
   - Multi-stage build (builder + runtime)
   - Python 3.11+ slim base image
   - Proper layer ordering for caching
   - Non-root user for security
   - Health checks
2. Generate `docker-compose.yml` with:
   - FastAPI service with auto-restart
   - PostgreSQL service with persistent volumes
   - Network configuration
   - Environment variable management
3. Create `.dockerignore` to exclude unnecessary files
4. Document build and run commands

---

## Implementation Patterns

### Async Database Operations

**Pattern**: Use SQLModel with async sessions for production performance.

```python
# Database connection with async support
from sqlmodel import create_engine, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    DATABASE_URL,
    echo=DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
```

### Error Handling

**Pattern**: Consistent error responses with proper HTTP status codes.

```python
from fastapi import HTTPException

# 404 Not Found
if not item:
    raise HTTPException(status_code=404, detail="Item not found")

# 409 Conflict (duplicate)
if existing:
    raise HTTPException(status_code=409, detail="Item already exists")

# 400 Bad Request (validation is automatic via Pydantic)
# 500 Internal Server Error (caught by exception handlers)
```

### Dependency Injection

**Pattern**: Use Annotated types for clean, reusable dependencies.

```python
from typing import Annotated
from fastapi import Depends

SessionDep = Annotated[AsyncSession, Depends(get_session)]

@app.get("/items/")
async def read_items(session: SessionDep):
    # Clean signature, session injected automatically
    return await session.exec(select(Item))
```

### Pagination

**Pattern**: Efficient pagination with skip and limit.

```python
from fastapi import Query

@app.get("/items/")
async def read_items(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    query = select(Item).offset(skip).limit(limit)
    return await session.exec(query).all()
```

### Response Models

**Pattern**: Separate schemas for input and output to control data exposure.

```python
class ItemCreate(SQLModel):
    name: str
    description: str | None = None

class ItemPublic(SQLModel):
    id: int
    name: str
    # Excludes internal fields like created_at for simple APIs

@app.post("/items/", response_model=ItemPublic)
async def create_item(item: ItemCreate, session: SessionDep):
    db_item = Item.from_orm(item)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Issue | Fix |
|--------------|-------|-----|
| Synchronous endpoints when async available | Blocks event loop, reduces concurrency | Use `async def`, async drivers |
| No pagination on list endpoints | Memory issues with large datasets | Always add skip/limit with reasonable defaults |
| Missing error handling | Unhandled exceptions return 500 | Use HTTPException with appropriate status codes |
| Shared database sessions | Thread-safety issues | Use dependency injection per-request |
| No input validation | Security and data integrity risk | Use Pydantic models for all input |
| Hard-coded database URLs | Secret exposure, inflexible | Use environment variables and config |
| No tests | Bugs catch in production | Always include test suite from start |
| Blocking operations in async context | Negates async benefits | Use async libraries (asyncpg, motor, etc.) |

---

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running (`docker-compose up -d postgres`)
- Check DATABASE_URL environment variable format
- Verify psycopg[asyncio] is installed for async support
- Use `pool_pre_ping=True` to detect stale connections

### Async/Await Errors
- Use `async def` for all path operations that perform I/O
- Use `await` for async function calls
- Don't mix sync and async drivers (use asyncpg, not psycopg2 raw)
- See `references/async-guide.md` for detailed patterns

### Import and Module Issues
- Run `pip install -r requirements.txt` after scaffolding
- Ensure package structure matches imports (use relative imports)
- Check `__init__.py` files exist in all package directories

### Docker Issues
- Build: `docker-compose build`
- Run: `docker-compose up`
- Logs: `docker-compose logs -f fastapi`
- Stop: `docker-compose down -v` (removes volumes)

---

## Next Steps After Scaffolding

1. **Verify project structure** - Check all generated files exist
2. **Install dependencies** - Run `pip install -r requirements.txt`
3. **Start database** - Run `docker-compose up -d postgres` or use local database
4. **Run application** - `fastapi dev app/main.py`
5. **View API docs** - Open http://localhost:8000/docs
6. **Run tests** - Execute `pytest` to verify generated tests pass
7. **Customize models** - Add your specific entities in `models/`
8. **Add endpoints** - Expand routers with domain-specific operations
9. **Implement business logic** - Add validation, calculations, workflows
10. **Deploy** - Build Docker image and deploy to your platform

---

## Key References

- `references/fastapi-patterns.md` - Common implementation patterns
- `references/sqlmodel-guide.md` - Database setup and async operations
- `references/testing-patterns.md` - Pytest integration testing strategies
- `references/docker-guide.md` - Production Docker configuration
- `references/async-guide.md` - Async/await best practices
- `references/environment-config.md` - Settings and environment variables

See the skill's references/ directory for detailed domain expertise documentation.
