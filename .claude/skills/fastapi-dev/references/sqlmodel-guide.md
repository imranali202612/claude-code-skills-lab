# SQLModel Integration Guide

SQLModel combines SQLAlchemy ORM and Pydantic validation in one model, eliminating schema duplication.

## Installation

```bash
pip install sqlmodel sqlalchemy psycopg[asyncio] alembic
```

## Database URL Patterns

### PostgreSQL (Recommended for Production)

```python
# Async PostgreSQL with asyncpg
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dbname"

# For Docker: host is the service name
DATABASE_URL = "postgresql+asyncpg://user:password@postgres:5432/dbname"
```

### SQLite (Development/Testing)

```python
# Synchronous SQLite (good for learning)
DATABASE_URL = "sqlite:///./test.db"

# Async SQLite
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
```

## Async Engine Setup

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,              # Set to True for SQL logging
    future=True,             # Use SQLAlchemy 2.0 API
    pool_pre_ping=True,      # Detect stale connections
    pool_size=20,            # Connections in pool
    max_overflow=10,         # Additional connections beyond pool
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)

# Dependency for FastAPI
async def get_session():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

## Model Definitions

### Single Model Approach

```python
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Hero(SQLModel, table=True):
    """Database model doubles as schema"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, min_length=1, max_length=100)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    secret_name: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Separate Models Approach (Recommended)

```python
from sqlmodel import Field, SQLModel

# Shared fields
class HeroBase(SQLModel):
    name: str = Field(index=True)
    age: Optional[int] = None
    secret_name: str

# Database model
class Hero(HeroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Input validation (create)
class HeroCreate(HeroBase):
    pass

# Partial update
class HeroUpdate(SQLModel):
    name: Optional[str] = None
    age: Optional[int] = None
    secret_name: Optional[str] = None

# Output/API response
class HeroPublic(HeroBase):
    id: int
    created_at: datetime
```

## Field Types and Constraints

```python
from sqlmodel import Field
from datetime import datetime
from typing import Optional

class Product(SQLModel, table=True):
    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Text fields
    name: str = Field(
        min_length=1,
        max_length=100,
        index=True,  # Add database index
        unique=True  # Unique constraint
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    # Numeric fields
    price: float = Field(gt=0, decimal_places=2)
    quantity: int = Field(ge=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)

    # Boolean field
    is_active: bool = Field(default=True)

    # Datetime fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Foreign key
    category_id: int = Field(foreign_key="category.id")
```

## Relationships

```python
from typing import List

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # One-to-many relationship
    posts: List["Post"] = Field(back_populates="author")

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author_id: int = Field(foreign_key="user.id")

    # Many-to-one relationship
    author: User = Field(back_populates="posts")
```

## Async Query Operations

```python
from sqlalchemy import select

# Create
async def create_hero(session: AsyncSession, hero: HeroCreate) -> Hero:
    db_hero = Hero.from_orm(hero)
    session.add(db_hero)
    await session.commit()
    await session.refresh(db_hero)
    return db_hero

# Read single
async def read_hero(session: AsyncSession, hero_id: int) -> Optional[Hero]:
    statement = select(Hero).where(Hero.id == hero_id)
    return await session.exec(statement).first()

# Read all with pagination
async def read_heroes(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 10
) -> List[Hero]:
    statement = select(Hero).offset(skip).limit(limit)
    return await session.exec(statement).all()

# Read with filter
async def read_heroes_by_age(
    session: AsyncSession,
    min_age: int
) -> List[Hero]:
    statement = select(Hero).where(Hero.age >= min_age)
    return await session.exec(statement).all()

# Update
async def update_hero(
    session: AsyncSession,
    hero_id: int,
    hero_update: HeroUpdate
) -> Optional[Hero]:
    db_hero = await session.get(Hero, hero_id)
    if not db_hero:
        return None

    update_data = hero_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_hero, key, value)

    session.add(db_hero)
    await session.commit()
    await session.refresh(db_hero)
    return db_hero

# Delete
async def delete_hero(session: AsyncSession, hero_id: int) -> bool:
    db_hero = await session.get(Hero, hero_id)
    if db_hero:
        await session.delete(db_hero)
        await session.commit()
        return True
    return False

# Count
async def count_heroes(session: AsyncSession) -> int:
    statement = select(func.count(Hero.id))
    return await session.exec(statement).one()
```

## Transaction Management

```python
async def transfer_credits(
    session: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    amount: float
) -> bool:
    try:
        from_user = await session.get(User, from_user_id)
        to_user = await session.get(User, to_user_id)

        if not from_user or not to_user:
            return False

        from_user.credits -= amount
        to_user.credits += amount

        session.add(from_user)
        session.add(to_user)

        await session.commit()
        return True

    except Exception:
        await session.rollback()
        return False
```

## Database Initialization

```python
async def init_db():
    """Create tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# In FastAPI lifespan
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

## Alembic Migrations

```bash
# Initialize
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add user table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### alembic/env.py configuration

```python
from app.models import SQLModel  # Import all models

# Set target_metadata
target_metadata = SQLModel.metadata
```

## Common Patterns

### Soft Delete Pattern

```python
from datetime import datetime

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    deleted_at: Optional[datetime] = Field(default=None)

async def delete_item(session: AsyncSession, item_id: int):
    """Soft delete"""
    item = await session.get(Item, item_id)
    if item:
        item.deleted_at = datetime.utcnow()
        session.add(item)
        await session.commit()

async def read_active_items(session: AsyncSession):
    """Only active items"""
    statement = select(Item).where(Item.deleted_at.is_(None))
    return await session.exec(statement).all()
```

### Timestamps Pattern

```python
from datetime import datetime

class BaseModel(SQLModel):
    """Base class with common fields"""
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Item(BaseModel, table=True):
    name: str
```

### Status Enum Pattern

```python
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
```

## Performance Considerations

1. **Connection Pooling**: Configured in engine creation (pool_size, max_overflow)
2. **Indexes**: Add `index=True` to frequently queried fields
3. **Eager Loading**: Use `selectinload()` for relationships to avoid N+1 queries
4. **Pagination**: Always use offset/limit for list endpoints
5. **Expire on Commit**: Set `expire_on_commit=False` for faster operations in async context
