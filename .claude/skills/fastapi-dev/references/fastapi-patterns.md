# FastAPI Implementation Patterns

## Project Structure Best Practices

### Standard Project Layout

```
fastapi-app/
├── app/
│   ├── __init__.py              # Package marker
│   ├── main.py                  # FastAPI app with routes
│   ├── config.py                # Settings, environment variables
│   ├── database.py              # Database connection, session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── item.py              # SQLModel database models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── item.py              # Pydantic request/response schemas
│   ├── crud/
│   │   ├── __init__.py
│   │   └── item.py              # Database operations (CRUD)
│   ├── routers/
│   │   ├── __init__.py
│   │   └── items.py             # API endpoints/routes
│   └── dependencies.py          # Shared dependencies
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and configuration
│   └── test_items.py            # Route tests
├── requirements.txt
├── .env.example
├── .env                         # (gitignored)
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
└── README.md
```

## Configuration Management Pattern

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "FastAPI App"
    debug: bool = False
    database_url: str = "sqlite:///./test.db"
    jwt_secret_key: str = "your-secret-key"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

# Usage in main.py
settings = get_settings()
```

## Database Session Management Pattern

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,      # Detects stale connections
    pool_size=20,            # Connection pool size
    max_overflow=10          # Max connections beyond pool_size
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

## Model Definition Pattern (SQLModel)

```python
# models/item.py
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class ItemBase(SQLModel):
    """Shared fields across all item schemas"""
    name: str = Field(index=True, min_length=1)
    description: Optional[str] = None
    price: float = Field(gt=0)

class Item(ItemBase, table=True):
    """Database table model"""
    __tablename__ = "items"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: int = Field(foreign_key="user.id")

class ItemCreate(ItemBase):
    """Request schema for creating items"""
    pass

class ItemUpdate(SQLModel):
    """Request schema for updating items"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)

class ItemPublic(ItemBase):
    """Response schema"""
    id: int
    created_at: datetime
```

## CRUD Operations Pattern

```python
# crud/item.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate

async def create_item(
    session: AsyncSession,
    item_in: ItemCreate,
    owner_id: int
) -> Item:
    """Create new item in database"""
    db_item = Item(**item_in.dict(), owner_id=owner_id)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item

async def read_item(session: AsyncSession, item_id: int) -> Optional[Item]:
    """Read single item by ID"""
    statement = select(Item).where(Item.id == item_id)
    return await session.exec(statement).first()

async def read_items(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 10
) -> list[Item]:
    """Read items with pagination"""
    statement = select(Item).offset(skip).limit(limit)
    return await session.exec(statement).all()

async def update_item(
    session: AsyncSession,
    item_id: int,
    item_in: ItemUpdate
) -> Optional[Item]:
    """Update item (partial)"""
    db_item = await read_item(session, item_id)
    if not db_item:
        return None

    update_data = item_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item

async def delete_item(session: AsyncSession, item_id: int) -> bool:
    """Delete item"""
    db_item = await read_item(session, item_id)
    if not db_item:
        return False

    await session.delete(db_item)
    await session.commit()
    return True
```

## Router/Endpoint Pattern

```python
# routers/items.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.item import ItemCreate, ItemPublic, ItemUpdate
from app.crud.item import (
    create_item,
    read_item,
    read_items,
    update_item,
    delete_item
)

router = APIRouter(prefix="/items", tags=["items"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]

@router.post("/", response_model=ItemPublic, status_code=status.HTTP_201_CREATED)
async def create_item_endpoint(
    item_in: ItemCreate,
    session: SessionDep
) -> ItemPublic:
    """Create a new item"""
    return await create_item(session, item_in, owner_id=1)

@router.get("/", response_model=list[ItemPublic])
async def list_items(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
) -> list[ItemPublic]:
    """List items with pagination"""
    return await read_items(session, skip, limit)

@router.get("/{item_id}", response_model=ItemPublic)
async def get_item(
    item_id: int,
    session: SessionDep
) -> ItemPublic:
    """Get single item by ID"""
    db_item = await read_item(session, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return db_item

@router.put("/{item_id}", response_model=ItemPublic)
async def update_item_endpoint(
    item_id: int,
    item_in: ItemUpdate,
    session: SessionDep
) -> ItemPublic:
    """Update item"""
    db_item = await update_item(session, item_id, item_in)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return db_item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_endpoint(
    item_id: int,
    session: SessionDep
) -> None:
    """Delete item"""
    success = await delete_item(session, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
```

## Application Setup Pattern

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers import items
from sqlmodel import SQLModel

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.app_name,
    description="Professional FastAPI application",
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

# Routes
app.include_router(items.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## Dependency Injection Pattern

```python
# dependencies.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Verify JWT token"""
    token = credentials.credentials
    # Verify token logic here
    return token

async def get_current_user(token: Annotated[str, Depends(verify_token)]) -> int:
    """Get current user from token"""
    # Decode token and extract user_id
    return 1

# Usage in router
CurrentUser = Annotated[int, Depends(get_current_user)]

@router.get("/me")
async def get_current_user_info(user_id: CurrentUser):
    return {"user_id": user_id}
```

## Lifespan Events Pattern

```python
# Handles startup and shutdown events
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code here
    print("Application starting up")
    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield  # Application runs

    # Shutdown code here
    print("Application shutting down")
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

## Exception Handler Pattern

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request, exc):
    return JSONResponse(
        status_code=409,
        content={"detail": "Duplicate entry or constraint violation"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## Type Hints and Validation

- Always use type hints for function parameters and returns
- Use Pydantic `Field` for constraints: `Field(gt=0, le=100, min_length=1)`
- Use `Optional` from `typing` for nullable fields
- Use `Annotated` for cleaner dependency injection
- Leverage automatic validation and OpenAPI schema generation
