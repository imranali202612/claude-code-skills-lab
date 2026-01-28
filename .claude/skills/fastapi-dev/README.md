# FastAPI Development Automation Skill

Production-grade skill for automating FastAPI project development from hello world to professional APIs.

## Quick Start

This skill automates the entire FastAPI development workflow:

```
User Request: "Create a FastAPI project for a todo API with PostgreSQL"
       ↓
Skill gathers requirements (project name, database, features)
       ↓
Scaffolds professional project structure
       ↓
Generates models, endpoints, tests, and Docker setup
       ↓
Production-ready application ready to customize
```

## What's Included

- **SKILL.md** (364 lines) - Main entry point with workflows and patterns
- **references/fastapi-patterns.md** (408 lines) - Implementation patterns and project structure
- **references/sqlmodel-guide.md** (387 lines) - Database setup and ORM patterns
- **references/async-guide.md** (318 lines) - Async/await best practices
- **references/testing-patterns.md** (423 lines) - Comprehensive testing strategies
- **references/docker-guide.md** (449 lines) - Production Docker configuration
- **scripts/scaffold_project.sh** - Automated project scaffolding

## When to Use

Invoke this skill when you need to:
- Initialize a new FastAPI project with professional structure
- Add database integration with PostgreSQL and SQLAlchemy/SQLModel
- Create CRUD endpoints with proper validation and error handling
- Set up testing infrastructure with pytest
- Configure Docker and deployment workflows
- Learn FastAPI best practices through generated code

## Key Features

✅ **Professional Project Structure** - Organized app, tests, configuration
✅ **Async-First Design** - Full async/await support for high performance
✅ **PostgreSQL Integration** - Async SQLModel ORM with connection pooling
✅ **Comprehensive Testing** - Pytest setup with fixtures and patterns
✅ **Production Docker** - Multi-stage build, non-root user, health checks
✅ **Environment Management** - .env configuration, secrets handling
✅ **Error Handling** - Proper HTTP status codes and exception patterns
✅ **Dependency Injection** - Type-safe, reusable dependencies
✅ **CORS Support** - Built-in middleware configuration
✅ **Auto-Documentation** - OpenAPI/Swagger integration

## Statistics

- **SKILL.md size**: 364 lines (well under 500 line limit)
- **Reference documentation**: 2,349 lines covering all major topics
- **Embedded expertise**: All patterns include working code examples
- **Domain coverage**: From hello world to production deployment

## Architecture

```
fastapi-dev/
├── SKILL.md                    # Entry point and workflows
├── references/
│   ├── fastapi-patterns.md     # Project structure, CRUD, routers
│   ├── sqlmodel-guide.md       # Database setup, migrations
│   ├── async-guide.md          # Async patterns and best practices
│   ├── testing-patterns.md     # Pytest fixtures and test patterns
│   └── docker-guide.md         # Docker, deployment, production
└── scripts/
    └── scaffold_project.sh     # Automated project scaffolding
```

## Generated Project Structure

When you use this skill to create a project:

```
my-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app with lifespan events
│   ├── config.py               # Settings management
│   ├── database.py             # Async session and engine setup
│   ├── dependencies.py         # Shared dependencies
│   ├── models/                 # SQLModel database models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── crud/                   # Database CRUD operations
│   └── routers/                # API endpoint groups
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   └── test_*.py               # Test files for each router
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .env                        # Development environment
├── Dockerfile                  # Production multi-stage build
├── docker-compose.yml          # PostgreSQL + app setup
└── README.md                   # Quick start guide
```

## Example Usage

### Initialize a new FastAPI project

```python
# Using the skill in Claude Code:
# User: "Create a FastAPI project for managing products with PostgreSQL"

# Skill will ask:
# 1. Project name? → "my-store"
# 2. Entities/models? → "products, categories, orders"
# 3. Additional features? → "authentication, rate limiting"
# 4. Deployment target? → "Docker + AWS"

# Result: Complete project structure with:
# ✓ Product CRUD endpoints with validation
# ✓ Database models with relationships
# ✓ Comprehensive tests
# ✓ Docker setup for easy deployment
```

## Domain Knowledge Embedded

This skill contains embedded expertise in:

1. **FastAPI Framework**
   - Type hints and automatic validation
   - Dependency injection patterns
   - Exception handling
   - Lifespan events

2. **SQLModel & Async ORM**
   - Async database operations
   - Model inheritance patterns
   - Query optimization
   - Connection pooling

3. **Async/Await Patterns**
   - When to use async vs sync
   - Event loop management
   - Concurrent operations
   - Error handling in async context

4. **Testing Strategies**
   - Pytest fixtures
   - Test database setup
   - Mocking dependencies
   - Async test execution

5. **Production Deployment**
   - Docker best practices
   - Multi-stage builds
   - Environment configuration
   - Security (non-root user, health checks)

## Next Steps

1. **Invoke the skill** in Claude Code with your project requirements
2. **Answer clarification questions** about project scope and preferences
3. **Receive scaffolded project** with all necessary structure
4. **Customize** models, endpoints, and business logic
5. **Deploy** using the included Docker configuration

---

**Skill Type**: Automation
**Recommended Model**: Claude Haiku 4.5 (sufficient for task automation)
**Use with**: FastAPI 0.108+, Python 3.10+, PostgreSQL 15+
**Status**: Production-ready
