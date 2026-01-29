# FastAPI Testing Patterns

## Database Fixtures with Transaction Rollback

When testing with a database, isolate each test by rolling back transactions:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient
from app import app, get_db

@pytest.fixture(scope="session")
def db_engine():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    # Create all tables
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)(Session)

    yield session

    # Rollback after test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

Usage:

```python
def test_create_user(client):
    response = client.post("/users/", json={"name": "Alice"})
    assert response.status_code == 201
    assert response.json()["name"] == "Alice"

def test_get_user(client):
    # Database is clean for this test
    response = client.get("/users/1")
    assert response.status_code == 404
```

## Async Endpoint Testing

FastAPI TestClient automatically handles async endpoints:

```python
@app.get("/async-endpoint/")
async def async_endpoint():
    await some_async_operation()
    return {"status": "done"}

def test_async_endpoint(client):
    response = client.get("/async-endpoint/")
    assert response.status_code == 200
```

For direct async test functions (without FastAPI), use `pytest-asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result is not None
```

## Authentication Testing

### Testing with Bearer Token

```python
@pytest.fixture
def auth_headers():
    token = "test-jwt-token"
    return {"Authorization": f"Bearer {token}"}

def test_protected_endpoint(client, auth_headers):
    response = client.get("/protected/", headers=auth_headers)
    assert response.status_code == 200

def test_protected_endpoint_without_auth(client):
    response = client.get("/protected/")
    assert response.status_code == 401
```

### Mocking Authentication

```python
from unittest.mock import patch

@patch("app.verify_token")
def test_with_mocked_auth(mock_verify, client):
    mock_verify.return_value = {"user_id": 123}
    response = client.get("/protected/")
    assert response.status_code == 200
```

## Dependency Injection in Tests

Override dependencies for testing:

```python
from fastapi import Depends

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Production dependency
    return verify_token(token)

@pytest.fixture
def client(db_session):
    async def override_get_current_user():
        return {"user_id": 123, "username": "testuser"}

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_endpoint_with_user(client):
    response = client.get("/user-endpoint/")
    assert response.status_code == 200
```

## Error Handling and Edge Cases

### Testing Validation Errors

```python
def test_invalid_request_body(client):
    response = client.post("/items/", json={"invalid": "data"})
    assert response.status_code == 422
    assert "detail" in response.json()

def test_item_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404
```

### Custom Error Responses

```python
@app.exception_handler(ItemNotFound)
async def item_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Item not found"},
    )

def test_custom_error_handler(client):
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"
```

## Parametrized API Testing

Test multiple endpoints and request combinations:

```python
@pytest.mark.parametrize("method,endpoint,status", [
    ("GET", "/items/", 200),
    ("POST", "/items/", 422),  # Missing required fields
    ("GET", "/items/999", 404),
])
def test_endpoints(client, method, endpoint, status):
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        response = client.post(endpoint, json={})

    assert response.status_code == status
```

## File Upload Testing

```python
from io import BytesIO

def test_file_upload(client):
    file_content = BytesIO(b"file content here")
    response = client.post(
        "/upload/",
        files={"file": ("test.txt", file_content)}
    )
    assert response.status_code == 200

def test_large_file_upload(client):
    large_content = BytesIO(b"x" * 10_000_000)
    response = client.post(
        "/upload/",
        files={"file": ("large.bin", large_content)}
    )
    assert response.status_code == 200
```

## Background Tasks Testing

```python
from fastapi import BackgroundTasks

@app.post("/send-notification/")
async def send_notification(
    message: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, message)
    return {"status": "notification queued"}

def test_background_task(client):
    with patch("app.send_email") as mock_send:
        response = client.post(
            "/send-notification/",
            json={"message": "Hello"}
        )
        assert response.status_code == 200
        # Background task was added
        mock_send.assert_called()
```
