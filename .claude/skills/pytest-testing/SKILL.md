---
name: pytest-testing
description: |
  Comprehensive pytest testing guidance for writing, organizing, and improving Python tests. Covers fixture patterns, assertions, async testing, parametrization, and framework-specific integration (FastAPI, Django). Use when writing or improving tests, debugging test failures, structuring test suites, or implementing advanced testing patterns.
---

# Pytest Testing

## Overview

Pytest is Python's most flexible testing framework. This skill provides patterns, best practices, and workflow guidance for writing effective tests—from basic unit tests to complex integration suites, including async testing for FastAPI and advanced fixture patterns.

## Quick Start

### Basic Test Structure

```python
def test_simple_addition():
    assert 2 + 2 == 4
```

For most tests, you need three elements:
1. **Setup** - Arrange test data and dependencies
2. **Action** - Execute the function or endpoint
3. **Assert** - Verify the result

```python
def test_user_creation():
    # Arrange
    user_data = {"name": "Alice", "email": "alice@example.com"}

    # Act
    user = create_user(user_data)

    # Assert
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
```

### Running Tests

```bash
pytest                          # Run all tests
pytest tests/                   # Run specific directory
pytest tests/test_models.py     # Run specific file
pytest -k "test_user"           # Run by name pattern
pytest -v                       # Verbose output
pytest --tb=short               # Shorter traceback
```

## Core Patterns

### Fixtures: Reusable Test Data

Fixtures provide isolated data to tests. Each test gets a fresh copy:

```python
@pytest.fixture
def sample_user():
    return {"name": "Bob", "email": "bob@example.com"}

def test_user_with_fixture(sample_user):
    assert sample_user["name"] == "Bob"

def test_another_user_with_fixture(sample_user):
    # Gets a fresh copy of sample_user
    assert sample_user["email"] == "bob@example.com"
```

**Fixture Scopes** (when to clean up):
- `function` (default) - Fresh fixture per test
- `class` - Shared across all methods in a test class
- `module` - Shared across all tests in a file
- `session` - Shared across entire test run

```python
@pytest.fixture(scope="session")
def database_connection():
    conn = connect_db()
    yield conn
    conn.close()  # Cleanup after all tests
```

### Factory Fixtures: Generate Multiple Test Objects

When you need multiple related objects:

```python
@pytest.fixture
def user_factory():
    def _make_user(name, email):
        return User(name=name, email=email)
    return _make_user

def test_multiple_users(user_factory):
    user1 = user_factory("Alice", "alice@example.com")
    user2 = user_factory("Bob", "bob@example.com")
    assert user1.name != user2.name
```

### Parametrization: Test Multiple Cases

Instead of writing duplicate tests, parametrize:

```python
@pytest.mark.parametrize("input,expected", [
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_square(input, expected):
    assert input ** 2 == expected
```

This runs three separate tests, one for each input/expected pair.

### Fixtures with Cleanup (Teardown)

Use `yield` for setup/cleanup:

```python
@pytest.fixture
def temp_file():
    # Setup
    filepath = "/tmp/test_file.txt"
    with open(filepath, "w") as f:
        f.write("test data")

    yield filepath  # Test receives this

    # Cleanup
    os.remove(filepath)
```

## FastAPI Testing

### TestClient: Testing Without a Running Server

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}

client = TestClient(app)

def test_get_item():
    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42}
```

### Testing POST Endpoints

```python
def test_create_item():
    response = client.post("/items/", json={"name": "Widget", "price": 9.99})
    assert response.status_code == 201
    assert response.json()["name"] == "Widget"
```

### Fixture for FastAPI Client

```python
@pytest.fixture
def client():
    return TestClient(app)

def test_endpoint_1(client):
    response = client.get("/")
    assert response.status_code == 200

def test_endpoint_2(client):
    response = client.post("/items/", json={"name": "Test"})
    assert response.status_code == 201
```

### Testing with Database (Using Async Fixtures)

See [FastAPI Testing Patterns](references/fastapi-testing.md) for:
- Database fixtures with transaction rollback
- Async endpoint testing
- Authentication and dependency injection testing
- Error handling and edge cases

## Assertion Strategies

### Common Assertions

```python
assert value == expected           # Equality
assert value is None               # None check
assert value is True               # Boolean
assert len(items) == 3             # Length
assert "substring" in "full string"  # Containment
assert isinstance(obj, MyClass)    # Type check
assert value > 10                  # Comparison
```

### Collections and Dicts

```python
assert response.json() == {"status": "ok"}
assert "key" in response.json()
assert len(response.json()["items"]) > 0
```

### Exception Testing

```python
import pytest

def test_raises_error():
    with pytest.raises(ValueError):
        invalid_function()

def test_specific_error_message():
    with pytest.raises(ValueError, match="expected error"):
        invalid_function()
```

## Test Organization

### Group Related Tests with Classes

```python
class TestUserCreation:
    def test_creates_user_with_valid_data(self):
        user = create_user({"name": "Alice"})
        assert user.name == "Alice"

    def test_raises_error_with_invalid_data(self):
        with pytest.raises(ValidationError):
            create_user({})

class TestUserDeletion:
    def test_deletes_user(self):
        user = create_user({"name": "Bob"})
        delete_user(user.id)
        assert get_user(user.id) is None
```

### conftest.py: Shared Fixtures

Create `tests/conftest.py` to share fixtures across multiple test files:

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Admin", "role": "admin"}

@pytest.fixture
def database():
    db = setup_test_db()
    yield db
    teardown_test_db()
```

All tests in the `tests/` directory can use these fixtures.

## Advanced Patterns

### Autouse Fixtures: Automatic Setup

```python
@pytest.fixture(autouse=True)
def reset_cache():
    # Runs before every test automatically
    cache.clear()
    yield
    # Cleanup after every test
    cache.clear()
```

### Mocking and Dependencies

See [Advanced Patterns](references/advanced-patterns.md) for:
- Mocking external services
- Dependency injection in tests
- Monkeypatching
- Spy functions and call tracking

### Async Testing

For async functions and endpoints, use `pytest-asyncio` or `anyio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await fetch_data()
    assert result is not None
```

For FastAPI, TestClient handles async automatically (see FastAPI Testing section above).

## Common Issues and Solutions

### "Fixture not found" Error
- Place fixture in `conftest.py` or same file as test
- Check spelling matches fixture name

### "Object has no attribute after fixture"
- Verify fixture scope matches usage
- Check fixture is being used (appears in function signature)

### Tests Run Slowly
- Check for unneeded `session` scope (accumulates state)
- Move to `function` scope for isolation
- Use fixtures with proper cleanup to avoid resource leaks

## Resources

### scripts/
- `conftest_template.py` - Reusable conftest template for new projects
- `fixture_generator.py` - Helper for creating common fixture patterns

### references/
- [FastAPI Testing Patterns](references/fastapi-testing.md) - Async fixtures, database testing, dependency injection
- [Advanced Patterns](references/advanced-patterns.md) - Mocking, parametrization, custom marks
- [Test Organization](references/test-organization.md) - Project structure, conftest strategy, sharing fixtures

## Resources

This skill includes example resource directories that demonstrate how to organize different types of bundled resources:

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Claude for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Claude's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Claude should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Claude produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Any unneeded directories can be deleted.** Not every skill requires all three types of resources.
