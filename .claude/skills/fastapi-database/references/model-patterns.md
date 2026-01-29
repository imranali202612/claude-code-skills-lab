# SQLModel and Pydantic Model Patterns

Reference for defining ORM models, relationships, and API schemas.

## Model Hierarchy

### Pattern: Base → Table → API Models

```python
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

# 1. Base: Shared fields between table and API
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: str
    is_active: bool = True

# 2. Table: Database model with ID and relationships
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str  # Internal only, not in API
    posts: list["Post"] = Relationship(back_populates="author")

# 3. Create: API request model for creation
class UserCreate(UserBase):
    password: str  # Takes plain password, never stored

# 4. Update: API request model for updates (all optional)
class UserUpdate(SQLModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

# 5. Public: API response model (excludes sensitive fields)
class UserPublic(UserBase):
    id: int

# 6. Full response: Includes relationships
class UserPublicWithPosts(UserPublic):
    posts: list["PostPublic"] = []
```

Why this pattern?
- **UserBase**: Single source of truth for shared fields
- **User (ORM)**: Maps to database table, includes all fields
- **UserCreate**: Defines what API accepts for POST
- **UserUpdate**: All fields optional for PATCH/PUT
- **UserPublic**: Never exposes `hashed_password` or database internals
- **UserPublicWithPosts**: Includes relationships when needed

## SQLModel Table Definitions

### Basic Table

```python
from typing import Optional
from sqlmodel import Field, SQLModel

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True)
    price: float = Field(gt=0)  # Price must be > 0
    inventory: int = Field(ge=0, default=0)  # >= 0
    description: Optional[str] = None
```

**Key Field parameters:**
- `primary_key=True` - Primary key
- `unique=True` - Unique constraint
- `index=True` - Create database index
- `default` - Default value on insert
- `nullable=False` - NOT NULL constraint
- `foreign_key="other_table.id"` - Foreign key

### Field Validation Constraints

```python
from sqlmodel import Field

class Product(SQLModel, table=True):
    # Numeric validation
    price: float = Field(gt=0, le=999999.99)  # > 0 and <= 999999.99
    rating: int = Field(ge=1, le=5)

    # String validation
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(regex=r"^[A-Z0-9]{6}$")  # 6 uppercase/digits

    # Database constraints
    email: str = Field(unique=True, index=True)
    category: str = Field(index=True, nullable=False)
```

## Relationships

### One-to-Many with Bidirectional Back-Populate

```python
class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    headquarters: str

    members: list["Member"] = Relationship(back_populates="team")

class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    team: Optional[Team] = Relationship(back_populates="members")
```

**Key points:**
- `foreign_key="team.id"` on the "many" side
- `Relationship(back_populates="...")` on both sides
- Forward reference as string: `"Team"` not `Team`

### One-to-One Relationship

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str

    profile: Optional["UserProfile"] = Relationship(back_populates="user")

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bio: str

    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="profile")
```

### Many-to-Many with Link Table

```python
class StudentCourse(SQLModel, table=True):
    """Link table for Student ↔ Course relationship"""
    student_id: Optional[int] = Field(default=None, foreign_key="student.id", primary_key=True)
    course_id: Optional[int] = Field(default=None, foreign_key="course.id", primary_key=True)

class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    courses: list["Course"] = Relationship(
        back_populates="students",
        link_model=StudentCourse
    )

class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    students: list["Student"] = Relationship(
        back_populates="courses",
        link_model=StudentCourse
    )
```

## API Response Models with Relationships

### Simple Response (No Relationships)

```python
@app.get("/teams/{team_id}", response_model=TeamPublic)
def get_team(team_id: int, session: SessionDep) -> TeamPublic:
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

# TeamPublic only includes basic fields
class TeamPublic(SQLModel):
    id: int
    name: str
    headquarters: str
```

### Response with Relationships

```python
# Define response models
class MemberPublic(SQLModel):
    id: int
    name: str

class TeamPublicWithMembers(SQLModel):
    id: int
    name: str
    headquarters: str
    members: list[MemberPublic] = []

@app.get("/teams/{team_id}", response_model=TeamPublicWithMembers)
def get_team(team_id: int, session: SessionDep) -> TeamPublicWithMembers:
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
```

## Update Operations

### Using sqlmodel_update()

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

    # Only update fields that were provided (not None)
    update_data = user_update.model_dump(exclude_unset=True)
    user.sqlmodel_update(update_data)

    session.add(user)
    session.commit()
    session.refresh(user)

    return user
```

**exclude_unset=True**: Only includes fields the user actually provided, skipping unset optional fields.

## Timestamps

### Auto-Set Created/Updated

```python
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

To update `updated_at` on modification:

```python
from datetime import datetime, timezone

post = session.get(Post, post_id)
post.updated_at = datetime.now(timezone.utc)
post.content = "Updated content"
session.add(post)
session.commit()
```

## Enums and Constraints

### String Enum

```python
from enum import Enum
from sqlmodel import Field, SQLModel

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    status: TaskStatus = Field(default=TaskStatus.PENDING)
```

### Usage in Routes

```python
@app.get("/tasks", response_model=list[TaskPublic])
def list_tasks(status: Optional[TaskStatus] = None, session: SessionDep):
    query = select(Task)
    if status:
        query = query.where(Task.status == status)
    return session.exec(query).all()

# Usage: /tasks?status=completed
```

## Default Values and Factories

```python
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Static default
    is_public: bool = Field(default=True)

    # Dynamic default (function called at insert time)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Optional with no default (NULL in database)
    description: Optional[str] = None
```

**Difference:**
- `default=value` - Static value, same for all rows
- `default_factory=callable` - Called for each row, useful for timestamps and UUIDs
