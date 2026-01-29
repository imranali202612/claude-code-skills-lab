---
name: fastapi-database
description: |
  Build production-grade FastAPI applications with database integration.
  This skill covers SQLModel ORM patterns, PostgreSQL/Neon connection setup, session management with dependency injection, CRUD operations, Pydantic request/response models, field validation, and HTTP status code semantics.
  Use this skill when implementing database-backed REST APIs, setting up database connections, defining models with relationships, handling validation, or debugging data layer issues.
allowed-tools: Read, Grep, Glob, Write, Edit
---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing project structure, database setup patterns, model conventions |
| **Conversation** | Your specific use case (CRUD for what entity?), database choice, API design needs |
| **Skill References** | SQLModel patterns, Pydantic validation, connection string formats in `references/` |
| **User Guidelines** | Project naming conventions, error handling preferences, authentication patterns |

Only ask about YOUR specific requirements (domain expertise is embedded in this skill).

---

## How This Skill Works

This skill provides structured patterns for:

1. **Database Setup** - Connection strings, engine configuration, session management
2. **Model Definition** - SQLModel ORM models, relationships, table creation
3. **Request/Response Schemas** - Pydantic models for API input/output, separation patterns
4. **Validation** - Field constraints, error responses, 422 vs 400 status codes
5. **CRUD Operations** - Create, read, update, delete patterns with proper error handling

Each section follows official FastAPI/SQLModel/Pydantic documentation patterns.

---

## Database Connection Setup

### Connection Strings

**PostgreSQL (Neon):**
```python
DATABASE_URL = "postgresql://user:password@host/database"
# Neon example: postgresql://user:password@ep-xyz.us-east-1.neon.tech/dbname
```

**SQLite (Development):**
```python
DATABASE_URL = "sqlite:///./test.db"
```

Configure engine with appropriate settings:

```python
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

# PostgreSQL with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set True for SQL logging in development
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
)

# SQLite (development only)
connect_args = {"check_same_thread": False}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)
```

### Session Dependency with Yield

**Correct pattern** - Uses `yield` for proper cleanup:

```python
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

Why `yield`? The code AFTER `yield` runs after the route returns, ensuring the session closes properly even if the route raises an exception.

### Database Initialization

```python
from fastapi import FastAPI

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
```

---

## SQLModel Table Definitions

### Base Model Pattern

Define a base class with common fields, then inherit for table and API models:

```python
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

class UserBase(SQLModel):
    """Shared fields between table and API models"""
    email: str = Field(unique=True, index=True)
    full_name: str
    is_active: bool = True

class User(UserBase, table=True):
    """Database table model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str  # Don't expose in API responses

    posts: list["Post"] = Relationship(back_populates="author")

class UserCreate(UserBase):
    """API request model for creation"""
    password: str  # Takes plain password, never stored here

class UserUpdate(SQLModel):
    """API request model for updates - all fields optional"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserPublic(UserBase):
    """API response model - excludes sensitive fields"""
    id: int
```

### Relationships

```python
class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str

    author_id: Optional[int] = Field(default=None, foreign_key="user.id")
    author: Optional[User] = Relationship(back_populates="posts")

class PostPublic(SQLModel):
    id: int
    title: str
    content: str
    author: UserPublic
```

### Indexes and Constraints

```python
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(unique=True, index=True)  # Unique index
    name: str = Field(index=True)  # Regular index
    price: float = Field(gt=0)  # Validation constraint
```

---

## Pydantic Request/Response Models

### Separation Pattern

**Never use ORM models directly in API responses** - exposes database details and secrets.

```python
# ❌ DON'T - Exposes ORM fields, database IDs, relationships
@app.post("/users/")
def create_user(user: User):  # User ORM model used directly
    ...

# ✅ DO - Separates concerns
@app.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate, session: SessionDep):
    ...
```

### Field Validation

Use `Field()` with constraints:

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr  # Built-in email validation
    password: str = Field(min_length=8, max_length=255)
    age: int = Field(ge=0, le=150)  # Greater/less than or equal
    bio: Optional[str] = Field(default=None, max_length=500)
```

**Field constraints:**
- `gt` / `lt` - Greater/less than
- `ge` / `le` - Greater/less than or equal
- `min_length` / `max_length` - String/list length
- `pattern` - Regex validation
- `default` / `default_factory` - Default values

### Validation Error Handling

Validation errors return **422 Unprocessable Entity**:

```python
from pydantic import ValidationError

try:
    user = UserCreate(email="invalid-email", password="short")
except ValidationError as e:
    # ValidationError.errors() returns list of error dicts
    for error in e.errors():
        print(error['loc'])      # ("email",) or ("password",)
        print(error['msg'])      # "value is not a valid email address"
        print(error['type'])     # "value_error.email"
```

FastAPI automatically converts ValidationError to 422 responses.

---

## HTTP Status Codes: 422 vs 400

### 422 Unprocessable Entity
**When**: Request syntax is valid JSON/form data, but **validation failed** against the schema.

```python
# Request: POST /users/
# Body: {"email": "not-an-email", "password": "short"}
# Status: 422
# Response: {"detail": [{"loc": ["body", "email"], "msg": "..."}]}

@app.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate):  # Pydantic validates here
    # If user data doesn't match UserCreate schema → 422
    pass
```

**FastAPI sends 422 automatically** when request body fails Pydantic validation.

### 400 Bad Request
**When**: Request syntax/parsing failed (malformed JSON, wrong content-type, etc).

```python
# Request: POST /users/
# Body: {not valid json}
# Status: 400
# Response: {"detail": "Invalid JSON"}

# Request: POST /users/
# Header: Content-Type: text/plain
# Status: 400
```

**Manually return 400** for business logic validation:

```python
from fastapi import HTTPException

@app.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate, session: SessionDep):
    # Pydantic already validated UserCreate schema (422)
    # Business logic validation → 400
    if session.exec(select(User).where(User.email == user.email)).first():
        raise HTTPException(
            status_code=400,
            detail="Email already registered"  # Business rule, not schema
        )
    ...
```

---

## CRUD Operations

### Create

```python
@app.post("/users/", response_model=UserPublic, status_code=201)
def create_user(user: UserCreate, session: SessionDep) -> UserPublic:
    # Pydantic validation happens here (422 on failure)

    # Business logic validation
    existing = session.exec(
        select(User).where(User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Create database model
    db_user = User(email=user.email, full_name=user.full_name)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user
```

### Read

```python
@app.get("/users/{user_id}", response_model=UserPublic)
def read_user(user_id: int, session: SessionDep) -> UserPublic:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=list[UserPublic])
def list_users(
    session: SessionDep,
    skip: int = 0,
    limit: int = 10,
) -> list[UserPublic]:
    users = session.exec(
        select(User).offset(skip).limit(limit)
    ).all()
    return users
```

### Update

```python
@app.put("/users/{user_id}", response_model=UserPublic)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: SessionDep,
) -> UserPublic:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only provided fields
    update_data = user_update.model_dump(exclude_unset=True)
    user.sqlmodel_update(update_data)
    session.add(user)
    session.commit()
    session.refresh(user)

    return user
```

### Delete

```python
@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: SessionDep) -> dict[str, bool]:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()

    return {"ok": True}
```

---

## Database Migrations

For production PostgreSQL databases, use **Alembic** (SQLAlchemy migration tool):

```bash
pip install alembic

# Initialize migrations
alembic init migrations

# Create migration
alembic revision --autogenerate -m "add user table"

# Apply migration
alembic upgrade head
```

For development/testing: `SQLModel.metadata.create_all(engine)` is acceptable.

---

## Error Handling Patterns

```python
from fastapi import HTTPException, status

# Resource not found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found"
)

# Business rule violation
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Email already registered"
)

# Authentication/authorization
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Not authorized to delete this resource"
)

# Database errors - return 500
from sqlalchemy.exc import IntegrityError

try:
    session.commit()
except IntegrityError:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database integrity error"
    )
```

---

## Key Patterns Summary

| Pattern | File | Usage |
|---------|------|-------|
| Connection setup | `references/connection-setup.md` | Database initialization, connection pooling |
| Model structure | `references/model-patterns.md` | Table, create, update, public schemas |
| Validation | `references/validation-patterns.md` | Field constraints, error types, status codes |
| CRUD examples | `references/crud-examples.md` | Create, read, update, delete operations |
| Migrations | `references/migration-guide.md` | Alembic setup and usage |

See reference files for complete examples and advanced patterns.
