# Database Connection Setup

Reference patterns for connecting FastAPI to PostgreSQL and other databases.

## PostgreSQL Connection Strings

### Neon (Serverless PostgreSQL)

```python
# Format: postgresql://[user]:[password]@[host]/[database]
DATABASE_URL = "postgresql://user:password@ep-xyz.us-east-1.neon.tech/dbname"

# With SSL (recommended for production)
DATABASE_URL = "postgresql://user:password@ep-xyz.us-east-1.neon.tech/dbname?sslmode=require"
```

### Standard PostgreSQL

```python
DATABASE_URL = "postgresql://user:password@localhost:5432/mydb"
```

### Environment Variables

```python
import os
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
    future=True,
)
```

## Engine Configuration

### PostgreSQL Production Setup

```python
from sqlalchemy import create_engine, pool

engine = create_engine(
    DATABASE_URL,
    # Connection pooling
    poolclass=pool.QueuePool,
    pool_size=5,
    max_overflow=10,
    # Health checks
    pool_pre_ping=True,  # Verify connections before reusing
    # Logging
    echo=False,  # Set True for SQL debugging
    future=True,
)
```

**pool_pre_ping=True**: Prevents "connection closed" errors from idle connections.

### SQLite Development Setup

```python
engine = create_engine(
    "sqlite:///./test.db",
    connect_args={"check_same_thread": False},
    echo=True,
)
```

**check_same_thread=False**: Allows multiple threads (FastAPI workers) to access SQLite. For production, use PostgreSQL.

## Session Management with Dependency Injection

### Basic Pattern

```python
from typing import Annotated
from fastapi import Depends, FastAPI
from sqlmodel import Session

def get_session():
    """
    Dependency that provides a database session.

    Uses 'yield' to ensure cleanup after request.
    Session commits are automatic on context exit if no exception occurs.
    """
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int, session: SessionDep):
    return session.get(User, user_id)
```

### Why Yield?

```python
def get_session():
    # Code BEFORE yield: setup
    with Session(engine) as session:
        yield session  # Return to route
        # Code AFTER yield: cleanup
        # Runs even if route raises exception
        # Session.close() happens here
```

## Database Initialization

### Startup Event

```python
from fastapi import FastAPI
from sqlmodel import SQLModel

def create_db_and_tables():
    """Create all tables defined with table=True"""
    SQLModel.metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
```

### Lifespan Context Manager (FastAPI 0.93+)

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown
    # Optional cleanup

app = FastAPI(lifespan=lifespan)
```

## Complete Setup Example

```python
from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select, Field

DATABASE_URL = "postgresql://user:password@localhost/mydb"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=5,
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Example model
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str

# Example route
@app.get("/users/{user_id}")
def read_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```
