# Pydantic Validation Patterns and HTTP Status Codes

Reference for validation, error handling, and HTTP status code semantics.

## Field Validation Constraints

### String Validation

```python
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    email: EmailStr  # Built-in email validation
    password: str = Field(
        min_length=8,
        max_length=255,
        pattern=r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$"  # At least 1 letter + 1 digit
    )
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$"  # Alphanumeric, dash, underscore
    )
    bio: str | None = Field(default=None, max_length=500)
```

### Numeric Validation

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    price: float = Field(gt=0, le=999999.99)  # > 0 and <= 999999.99
    quantity: int = Field(ge=0, le=10000)  # >= 0 and <= 10000
    rating: int = Field(ge=1, le=5)
    discount_percent: float = Field(ge=0, le=100)
```

**Comparison operators:**
- `gt` - Greater than (>)
- `ge` - Greater than or equal (>=)
- `lt` - Less than (<)
- `le` - Less than or equal (<=)

### List Validation

```python
from typing import Optional
from pydantic import BaseModel, Field

class BlogPost(BaseModel):
    tags: list[str] = Field(
        min_length=1,
        max_length=10,
        default_factory=list
    )
    # Also validate individual items
    emails: list[EmailStr] = Field(
        min_length=1,
        max_length=50
    )
```

### Custom Validation with model_validator

```python
from pydantic import BaseModel, field_validator, model_validator

class UserUpdate(BaseModel):
    password: str | None = None
    password_confirm: str | None = None

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password or self.password_confirm:
            if self.password != self.password_confirm:
                raise ValueError("Passwords do not match")
        return self

# Usage
try:
    user = UserUpdate(password="secret123", password_confirm="secret456")
except ValidationError as e:
    print(e.errors())
    # [{'type': 'value_error', 'msg': 'Passwords do not match', ...}]
```

### Field Validator (Per-Field)

```python
from pydantic import BaseModel, field_validator

class Product(BaseModel):
    sku: str
    name: str

    @field_validator('sku')
    @classmethod
    def sku_must_be_uppercase(cls, v):
        if not v.isupper():
            raise ValueError('SKU must be uppercase')
        return v

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
```

## Validation Errors

### Understanding ValidationError

```python
from pydantic import BaseModel, ValidationError, Field, EmailStr

class User(BaseModel):
    email: EmailStr
    age: int = Field(ge=0, le=150)

try:
    user = User(email="invalid-email", age="not-a-number")
except ValidationError as e:
    # e.errors() returns list of error dictionaries
    for error in e.errors():
        print(error)
        # {
        #   'type': 'value_error.email',
        #   'loc': ('email',),
        #   'msg': 'value is not a valid email address',
        #   'input': 'invalid-email',
        #   'ctx': {'reason': 'The email address is not valid...'}
        # }
```

### Error Structure

Each error dict contains:
- `type` - Error type (e.g., 'value_error', 'type_error', 'assertion_error')
- `loc` - Tuple showing field path: `('field',)` or `('nested', 'field')`
- `msg` - Human-readable error message
- `input` - The value that failed validation
- `ctx` - Additional context (optional)

## HTTP Status Code Semantics

### 422 Unprocessable Entity (Validation Error)

**When it's sent:**
- Request has valid JSON/form syntax
- Data types are correct
- But Pydantic schema validation FAILS

**FastAPI sends automatically:**
```python
@app.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate):  # Pydantic validates here
    # If user data doesn't match UserCreate schema → FastAPI returns 422
    pass
```

**Request → 422 Response:**
```
POST /users/
Body: {"email": "not-an-email", "password": "short"}

Response 422:
{
  "detail": [
    {
      "type": "value_error.email",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "input": "not-an-email"
    },
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "short"
    }
  ]
}
```

### 400 Bad Request

**When it's sent:**
- Request parsing failed (malformed JSON)
- Wrong content-type
- **OR** business logic validation failed (not schema validation)

**Malformed JSON → 400:**
```
POST /users/
Body: {not valid json}

Response 400:
{
  "detail": "Invalid JSON"
}
```

**Business validation → 400:**
```python
from fastapi import HTTPException

@app.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate, session: SessionDep):
    # Pydantic already validated schema (422 on failure)

    # Business logic: is email already taken?
    existing = session.exec(
        select(User).where(User.email == user.email)
    ).first()
    if existing:
        # Email is valid (would pass 422), but violates business rule
        raise HTTPException(
            status_code=400,  # 400 not 422
            detail="Email already registered"
        )
    ...
```

### Status Code Comparison

| Status | Meaning | Example |
|--------|---------|---------|
| **422** | Schema validation failed | `{"email": "not valid"}` |
| **400** | Business logic failed | `{"detail": "Email already registered"}` |
| **404** | Resource not found | User ID doesn't exist |
| **409** | Conflict (e.g., duplicate) | Unique constraint violation |
| **500** | Server error | Database connection failed |

## FastAPI Validation Error Handling

### Override Default 422 Response

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

app = FastAPI()

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    # Custom error format
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "errors": exc.errors(),
        },
    )
```

### Custom Status Code for Validation

**By default, Pydantic validation errors → 422.**
You can't change this globally, but you can use business logic validation → 400:

```python
from fastapi import HTTPException, status

@app.post("/users/", response_model=UserPublic)
def create_user(user: UserCreate, session: SessionDep):
    # Schema validation (422) already passed if we reach here

    # Business validation (400)
    if not user.email.endswith("@company.com"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email must be from @company.com domain"
        )
    ...
```

## Real-World Validation Example

```python
from datetime import date
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator

class PersonCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    birth_date: date
    phone: str = Field(pattern=r"^\+?1?\d{9,15}$")

    @field_validator("first_name", "last_name")
    @classmethod
    def names_not_numbers(cls, v):
        if v.isdigit():
            raise ValueError("Name cannot be only numbers")
        return v.title()  # Capitalize

    @model_validator(mode="after")
    def valid_birth_date(self):
        today = date.today()
        age = today.year - self.birth_date.year
        if age < 18:
            raise ValueError("Must be at least 18 years old")
        if age > 150:
            raise ValueError("Birth date seems invalid")
        return self

# Test with FastAPI
from fastapi import FastAPI

app = FastAPI()

@app.post("/people/")
def create_person(person: PersonCreate):
    # All validations run here:
    # - email format (422 on failure)
    # - name lengths (422 on failure)
    # - phone format (422 on failure)
    # - names not numbers (422 on failure)
    # - valid birth date and age (422 on failure)
    return person
```

## Validation in Request/Response Separation

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    """What API accepts"""
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)

class UserPublic(BaseModel):
    """What API returns"""
    id: int
    email: str
    full_name: str
    # Note: password and hashed_password NOT included
```

**Client sends UserCreate → Validated by Pydantic (422 on error)**
**API returns UserPublic → Different schema, secure**
