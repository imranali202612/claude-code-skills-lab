# FastAPI Async/Await Best Practices

Understanding when and how to use async in FastAPI is critical for performance.

## Core Concepts

### Event Loop Basics

```python
# FastAPI runs on Uvicorn (uses asyncio event loop)
# Event loop executes coroutines efficiently by switching between them
# when they hit I/O operations (database, network, file reads)
```

### When to Use `async def` vs `def`

| Pattern | Use `async def` | Use `def` |
|---------|-----------------|----------|
| **I/O Operations** | Database queries, HTTP calls, file reads | CPU-bound calculations |
| **Performance** | High concurrency, multiple concurrent requests | Blocking operations |
| **External APIs** | Async libraries (httpx, asyncpg, motor) | Sync libraries (requests, psycopg2) |
| **Database** | Async drivers (asyncpg, aiosqlite) | Sync drivers (psycopg2) |

## Patterns and Examples

### Async Endpoint with Database

```python
# CORRECT: Async endpoint with async database
@app.get("/items/{item_id}")
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    """Best for production"""
    # Event loop can handle other requests while waiting for DB
    statement = select(Item).where(Item.id == item_id)
    item = await session.exec(statement).first()
    if not item:
        raise HTTPException(status_code=404)
    return item


# WRONG: Sync endpoint with async database
@app.get("/items/{item_id}")
def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    """Don't do this - defeats async benefits"""
    # Blocks entire thread
    item = session.exec(select(Item).where(Item.id == item_id)).first()
    return item
```

### Async with External API Calls

```python
import httpx
from fastapi import FastAPI

app = FastAPI()

@app.post("/users/")
async def create_user(user: UserCreate):
    """Fetch user data from external API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user.email}")
        external_data = response.json()

    # Save to database
    db_user = User(**user.dict(), external_id=external_data["id"])
    # ... save to db
    return db_user
```

### Mixed Sync and Async (When Necessary)

```python
# Endpoint can accept sync functions via dependency injection
def compute_score(data: list[int]) -> float:
    """CPU-bound operation - pure function"""
    return sum(data) / len(data)

@app.post("/scores/")
async def calculate_score(data: list[int]):
    """Async endpoint calling sync function"""
    # Pure sync function doesn't block much
    score = compute_score(data)

    # Then do async operations
    # Store in database
    # ...
    return {"score": score}
```

### Dependency with Async

```python
from typing import Annotated

# Async dependency
async def get_current_user(token: str = Header()) -> User:
    """Async dependency"""
    user = await authenticate_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

# Use in endpoint
CurrentUser = Annotated[User, Depends(get_current_user)]

@app.get("/me/")
async def get_current_user_info(user: CurrentUser):
    """Token is verified via async dependency"""
    return user
```

### List Multiple Items with Pagination

```python
# CORRECT: Async with efficient queries
@app.get("/items/")
async def list_items(
    session: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Load items efficiently"""
    statement = (
        select(Item)
        .offset(skip)
        .limit(limit)
        .order_by(Item.created_at.desc())
    )
    items = await session.exec(statement).all()
    return items
```

### Background Tasks Pattern

```python
from fastapi import BackgroundTasks

@app.post("/items/")
async def create_item(
    item: ItemCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
):
    """Create item and send email in background"""
    # Create item
    db_item = Item(**item.dict())
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)

    # Send email in background (don't wait)
    background_tasks.add_task(send_email, db_item.id, "created")

    return db_item

async def send_email(item_id: int, action: str):
    """Background task - runs after response"""
    # Don't need to be super fast here
    item = await get_item(item_id)
    # Email sending logic
```

### Concurrent Operations

```python
import asyncio

@app.get("/data/")
async def get_combined_data():
    """Fetch from multiple sources concurrently"""
    # Execute all three operations concurrently
    users, posts, comments = await asyncio.gather(
        fetch_users(),
        fetch_posts(),
        fetch_comments()
    )
    return {
        "users": users,
        "posts": posts,
        "comments": comments
    }

async def fetch_users():
    # Simulates async I/O
    await asyncio.sleep(0.5)
    return ["user1", "user2"]

async def fetch_posts():
    await asyncio.sleep(0.3)
    return ["post1", "post2"]

async def fetch_comments():
    await asyncio.sleep(0.2)
    return ["comment1", "comment2"]
# Total time: ~0.5s (concurrent), not 1s (sequential)
```

## Common Issues and Solutions

### Issue: "RuntimeError: no running event loop"

**Problem**: Trying to use `async` code outside event loop

```python
# WRONG
def my_function():
    await some_async_function()  # Error!

# CORRECT
async def my_function():
    await some_async_function()

# Or in sync context
import asyncio
result = asyncio.run(some_async_function())
```

### Issue: Mixing Blocking Calls in Async

```python
# WRONG: Blocking library in async context
@app.get("/items/")
async def get_items():
    import time
    time.sleep(1)  # BLOCKS entire event loop!
    return []

# CORRECT: Use async operations
@app.get("/items/")
async def get_items():
    import asyncio
    await asyncio.sleep(1)  # Non-blocking
    return []

# Or use run_in_threadpool for blocking operations
from fastapi import BackgroundTasks

@app.get("/compute/")
async def heavy_computation(background_tasks: BackgroundTasks):
    """Offload blocking work"""
    # Long-running CPU-bound operation
    background_tasks.add_task(expensive_calculation)
    return {"status": "processing"}
```

### Issue: Forgot to Await

```python
# WRONG
@app.get("/users/")
async def get_users(session: AsyncSession):
    # Returns coroutine object, not the result!
    users = session.exec(select(User)).all()
    return users

# CORRECT
@app.get("/users/")
async def get_users(session: AsyncSession):
    users = await session.exec(select(User)).all()
    return users
```

## Performance Implications

### With 100 Concurrent Requests

**Pure Async Implementation**:
- Each request waits for I/O independently
- Event loop switches between requests during I/O waits
- Total time: ~500ms (longest single request)
- CPU usage: Minimal (mostly I/O waiting)

**Mixed Sync/Blocking**:
- Requests block each other
- Thread pool exhaustion possible
- Total time: ~50s (sequential requests)
- CPU usage: Idle threads waiting

### Benchmarks

```
GET /users - 10ms DB query

Async Implementation:
- 100 requests: ~50ms total (limited by DB)
- Handles 1000s concurrent

Sync Implementation:
- 100 requests: ~1s total (sequential)
- Limited by thread pool size (~50-100 threads)
```

## Best Practices

1. **Always use `async def` for FastAPI endpoints**
   - Even if you don't use await, it signals the framework

2. **Use async database drivers**
   - PostgreSQL: `asyncpg` (not `psycopg2`)
   - MySQL: `aiomysql` or `asyncmy`
   - SQLite: `aiosqlite`

3. **Use async HTTP client**
   - `httpx.AsyncClient()` instead of `requests`

4. **Avoid blocking operations**
   - If necessary, use `BackgroundTasks`
   - Or run in thread pool with `loop.run_in_executor()`

5. **Use `asyncio.gather()` for concurrent operations**
   - Fetch from multiple sources efficiently

6. **Always `await` async functions**
   - Forgetting breaks your code silently

7. **Test async code properly**
   - Use `pytest-asyncio` for async tests
