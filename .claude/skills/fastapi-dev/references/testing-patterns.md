# FastAPI Testing Patterns

Professional testing strategy for FastAPI applications using pytest.

## Test Setup with Fixtures

### conftest.py - Core Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.main import app
from app.database import get_session, engine as prod_engine

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

@pytest.fixture
def client(test_session):
    """TestClient with overridden dependencies"""
    def override_get_session():
        return test_session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()

# Test data fixtures
@pytest.fixture
async def sample_hero(test_session):
    """Create sample hero"""
    from app.models.hero import Hero

    hero = Hero(
        name="Deadpond",
        secret_name="Dive Wilson",
        age=None,
    )
    test_session.add(hero)
    await test_session.commit()
    await test_session.refresh(hero)
    return hero

@pytest.fixture
async def sample_heroes(test_session):
    """Create multiple heroes"""
    from app.models.hero import Hero

    heroes = [
        Hero(name="Hero 1", secret_name="Secret 1"),
        Hero(name="Hero 2", secret_name="Secret 2"),
        Hero(name="Hero 3", secret_name="Secret 3"),
    ]
    for hero in heroes:
        test_session.add(hero)
    await test_session.commit()
    return heroes
```

### pytest.ini Configuration

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

## Test Patterns by Endpoint Type

### Testing Create (POST)

```python
# tests/test_heroes.py
import pytest

@pytest.mark.asyncio
async def test_create_hero(client):
    """Test successful hero creation"""
    response = client.post(
        "/heroes/",
        json={
            "name": "Deadpond",
            "secret_name": "Dive Wilson",
            "age": 30,
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Deadpond"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_create_hero_missing_required_field(client):
    """Test validation error on missing field"""
    response = client.post(
        "/heroes/",
        json={
            "secret_name": "Dive Wilson",
            # Missing "name"
        }
    )
    assert response.status_code == 422
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_create_hero_duplicate(client, sample_hero):
    """Test conflict error on duplicate"""
    response = client.post(
        "/heroes/",
        json={
            "name": sample_hero.name,
            "secret_name": "Other",
        }
    )
    # Depending on implementation
    assert response.status_code in [400, 409]
```

### Testing Read (GET) - Single Item

```python
@pytest.mark.asyncio
async def test_get_hero(client, sample_hero):
    """Test successful retrieval"""
    response = client.get(f"/heroes/{sample_hero.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_hero.id
    assert data["name"] == sample_hero.name

@pytest.mark.asyncio
async def test_get_hero_not_found(client):
    """Test 404 when hero doesn't exist"""
    response = client.get("/heroes/999")
    assert response.status_code == 404
```

### Testing Read (GET) - List

```python
@pytest.mark.asyncio
async def test_list_heroes(client, sample_heroes):
    """Test list with pagination"""
    response = client.get("/heroes/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

@pytest.mark.asyncio
async def test_list_heroes_pagination(client, sample_heroes):
    """Test pagination parameters"""
    response = client.get("/heroes/?skip=1&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Hero 2"

@pytest.mark.asyncio
async def test_list_heroes_empty(client):
    """Test empty list"""
    response = client.get("/heroes/")
    assert response.status_code == 200
    assert response.json() == []
```

### Testing Update (PUT/PATCH)

```python
@pytest.mark.asyncio
async def test_update_hero(client, sample_hero):
    """Test successful update"""
    response = client.put(
        f"/heroes/{sample_hero.id}",
        json={
            "name": "Updated Name",
            "secret_name": "Updated Secret",
            "age": 35,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["age"] == 35

@pytest.mark.asyncio
async def test_partial_update_hero(client, sample_hero):
    """Test partial update (PATCH)"""
    response = client.patch(
        f"/heroes/{sample_hero.id}",
        json={"age": 40}  # Only update age
    )
    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 40
    assert data["name"] == sample_hero.name  # Unchanged

@pytest.mark.asyncio
async def test_update_hero_not_found(client):
    """Test 404 on update"""
    response = client.put(
        "/heroes/999",
        json={"name": "Updated"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_hero_invalid_data(client, sample_hero):
    """Test validation error"""
    response = client.put(
        f"/heroes/{sample_hero.id}",
        json={
            "name": "",  # Invalid: min_length=1
            "secret_name": "Valid",
        }
    )
    assert response.status_code == 422
```

### Testing Delete (DELETE)

```python
@pytest.mark.asyncio
async def test_delete_hero(client, sample_hero):
    """Test successful deletion"""
    response = client.delete(f"/heroes/{sample_hero.id}")
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/heroes/{sample_hero.id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_hero_not_found(client):
    """Test 404 on delete"""
    response = client.delete("/heroes/999")
    assert response.status_code == 404
```

## Authentication Testing

```python
@pytest.fixture
def auth_headers():
    """Headers with valid token"""
    return {"Authorization": "Bearer valid-token"}

@pytest.mark.asyncio
async def test_endpoint_requires_auth(client):
    """Test 401 without token"""
    response = client.get("/protected/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_endpoint_with_auth(client, auth_headers):
    """Test successful with token"""
    response = client.get("/protected/", headers=auth_headers)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_invalid_token(client):
    """Test 401 with invalid token"""
    response = client.get(
        "/protected/",
        headers={"Authorization": "Bearer invalid-token"}
    )
    assert response.status_code == 401
```

## Database Transaction Testing

```python
@pytest.mark.asyncio
async def test_transaction_rollback(test_session):
    """Test rollback on error"""
    from app.models.hero import Hero

    try:
        hero = Hero(name="Test", secret_name="Test")
        test_session.add(hero)

        # Simulate error
        raise Exception("Simulated error")

        await test_session.commit()
    except Exception:
        await test_session.rollback()

    # Verify hero wasn't saved
    count = await test_session.exec(
        select(func.count(Hero.id))
    ).one()
    assert count == 0
```

## Async Test Execution

```python
# Mark tests as async
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None

# Or use pytest-asyncio with autouse
@pytest.mark.asyncio
async def test_database_insert(test_session):
    from app.models.hero import Hero

    hero = Hero(name="Test", secret_name="Test")
    test_session.add(hero)
    await test_session.commit()

    # Verify
    heroes = await test_session.exec(select(Hero)).all()
    assert len(heroes) == 1
```

## Integration Testing

```python
@pytest.mark.asyncio
async def test_create_and_retrieve_hero(client):
    """Full integration test"""
    # Create
    create_response = client.post(
        "/heroes/",
        json={
            "name": "Deadpond",
            "secret_name": "Dive Wilson",
        }
    )
    assert create_response.status_code == 201
    hero_id = create_response.json()["id"]

    # Retrieve
    get_response = client.get(f"/heroes/{hero_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Deadpond"

    # Update
    update_response = client.put(
        f"/heroes/{hero_id}",
        json={"age": 30}
    )
    assert update_response.status_code == 200

    # List and verify
    list_response = client.get("/heroes/")
    assert len(list_response.json()) == 1
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_heroes.py

# Run specific test
pytest tests/test_heroes.py::test_create_hero

# Verbose output
pytest -v

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Coverage report
pytest --cov=app tests/
```

## requirements-dev.txt

```
pytest>=7.0
pytest-asyncio>=0.21.0
httpx>=0.23.0
```
