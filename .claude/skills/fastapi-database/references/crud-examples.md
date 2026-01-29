# CRUD Operations - Complete Examples

Production-ready CRUD patterns with error handling and validation.

## Complete Setup

```python
from typing import Annotated, Optional
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import create_engine, select
from sqlmodel import Field, Session, SQLModel

# Database
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Models
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: str
    is_active: bool = True

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(SQLModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserPublic(UserBase):
    id: int
    created_at: datetime

# App
app = FastAPI()

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
```

## Create (POST)

### Basic Create

```python
@app.post("/users/", response_model=UserPublic, status_code=201)
def create_user(user: UserCreate, session: SessionDep) -> UserPublic:
    """Create a new user."""

    # Pydantic validation (422 on failure)
    # Already done by FastAPI before this function is called

    # Business logic validation (400 on failure)
    existing = session.exec(
        select(User).where(User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        hashed_password=f"hashed_{user.password}"  # In real code, use bcrypt
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user
```

### Create with Relationships

```python
class PostCreate(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=10)
    author_id: int

class PostPublic(SQLModel):
    id: int
    title: str
    content: str
    author_id: int

@app.post("/posts/", response_model=PostPublic, status_code=201)
def create_post(post: PostCreate, session: SessionDep) -> PostPublic:
    """Create a new post for an author."""

    # Verify author exists
    author = session.get(User, post.author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found"
        )

    # Create
    db_post = Post(
        title=post.title,
        content=post.content,
        author_id=post.author_id
    )
    session.add(db_post)
    session.commit()
    session.refresh(db_post)

    return db_post
```

## Read (GET)

### Get Single Resource

```python
@app.get("/users/{user_id}", response_model=UserPublic)
def read_user(user_id: int, session: SessionDep) -> UserPublic:
    """Get a user by ID."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
```

### List with Pagination

```python
@app.get("/users/", response_model=list[UserPublic])
def list_users(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
) -> list[UserPublic]:
    """Get all users with pagination."""
    users = session.exec(
        select(User).offset(skip).limit(limit)
    ).all()
    return users
```

### List with Filtering

```python
@app.get("/users/", response_model=list[UserPublic])
def list_users(
    session: SessionDep,
    is_active: Optional[bool] = None,
    email: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
) -> list[UserPublic]:
    """Get users with optional filters."""
    query = select(User)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    if email:
        query = query.where(User.email.ilike(f"%{email}%"))

    users = session.exec(query.offset(skip).limit(limit)).all()
    return users
```

### List with Sorting

```python
@app.get("/users/", response_model=list[UserPublic])
def list_users(
    session: SessionDep,
    sort_by: str = Query("created_at", regex="^(created_at|full_name|email)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    limit: int = Query(10, ge=1, le=100),
) -> list[UserPublic]:
    """Get users with sorting."""
    from sqlalchemy import desc

    query = select(User)

    if sort_by == "created_at":
        col = User.created_at
    elif sort_by == "full_name":
        col = User.full_name
    else:
        col = User.email

    if order == "desc":
        query = query.order_by(desc(col))
    else:
        query = query.order_by(col)

    users = session.exec(query.limit(limit)).all()
    return users
```

## Update (PUT/PATCH)

### Full Update (PUT)

```python
@app.put("/users/{user_id}", response_model=UserPublic)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: SessionDep,
) -> UserPublic:
    """Fully update a user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check email uniqueness if changing
    if user_update.email and user_update.email != user.email:
        existing = session.exec(
            select(User).where(User.email == user_update.email)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Update only provided fields
    update_data = user_update.model_dump(exclude_unset=True)
    user.sqlmodel_update(update_data)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user
```

### Partial Update (PATCH)

PATCH is semantically the same as PUT in this example. The difference is:
- PUT: Client sends complete resource (all fields required)
- PATCH: Client sends partial update (only changed fields)

```python
# PATCH: All fields in schema are optional by default
@app.patch("/users/{user_id}", response_model=UserPublic)
def partial_update_user(
    user_id: int,
    user_update: UserUpdate,  # All fields optional
    session: SessionDep,
) -> UserPublic:
    """Partially update a user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    update_data = user_update.model_dump(exclude_unset=True)
    user.sqlmodel_update(update_data)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user
```

## Delete (DELETE)

### Simple Delete

```python
@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: SessionDep) -> dict[str, bool]:
    """Delete a user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    session.delete(user)
    session.commit()

    return {"ok": True}
```

### Delete with Cascade Considerations

```python
@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: SessionDep) -> dict[str, bool]:
    """Delete a user and their related posts."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # If database has cascade delete configured, just delete user
    # Otherwise, manually delete related posts
    posts = session.exec(select(Post).where(Post.author_id == user_id)).all()
    for post in posts:
        session.delete(post)

    session.delete(user)
    session.commit()

    return {"ok": True}
```

## Bulk Operations

### Bulk Create

```python
class UserListCreate(SQLModel):
    users: list[UserCreate]

@app.post("/users/bulk/", response_model=list[UserPublic], status_code=201)
def create_users_bulk(
    data: UserListCreate,
    session: SessionDep,
) -> list[UserPublic]:
    """Create multiple users."""

    # Validate no duplicate emails
    emails = [u.email for u in data.users]
    if len(emails) != len(set(emails)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate emails in request"
        )

    # Check for existing emails
    existing = session.exec(
        select(User).where(User.email.in_(emails))
    ).all()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some emails already registered"
        )

    # Create all
    db_users = []
    for user in data.users:
        db_user = User(
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            hashed_password=f"hashed_{user.password}"
        )
        db_users.append(db_user)

    session.add_all(db_users)
    session.commit()

    # Refresh all
    for db_user in db_users:
        session.refresh(db_user)

    return db_users
```

### Bulk Delete

```python
class IDList(SQLModel):
    ids: list[int]

@app.delete("/users/bulk/")
def delete_users_bulk(data: IDList, session: SessionDep) -> dict[str, int]:
    """Delete multiple users."""
    users = session.exec(
        select(User).where(User.id.in_(data.ids))
    ).all()

    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found with provided IDs"
        )

    count = len(users)
    for user in users:
        session.delete(user)
    session.commit()

    return {"deleted": count}
```

## Error Handling Patterns

```python
from sqlalchemy.exc import IntegrityError

@app.post("/users/", response_model=UserPublic, status_code=201)
def create_user(user: UserCreate, session: SessionDep) -> UserPublic:
    """Create user with comprehensive error handling."""

    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=f"hashed_{user.password}"
    )
    session.add(db_user)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists (database constraint)"
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )

    session.refresh(db_user)
    return db_user
```
