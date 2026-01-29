# Advanced Pytest Patterns

## Mocking External Services

### Using unittest.mock

```python
from unittest.mock import patch, MagicMock

@patch("app.requests.get")
def test_with_mocked_request(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": "value"}

    result = fetch_external_api()
    assert result == {"data": "value"}
    mock_get.assert_called_once()
```

### Mocking Entire Modules

```python
@patch("app.external_service")
def test_service_failure(mock_service):
    mock_service.side_effect = ConnectionError("Service down")

    with pytest.raises(ConnectionError):
        call_external_service()
```

### Fixture-Based Mocking

```python
@pytest.fixture
def mock_database():
    with patch("app.database") as mock_db:
        mock_db.query.return_value = [{"id": 1, "name": "Test"}]
        yield mock_db

def test_with_mock_database(mock_database):
    result = get_all_records()
    assert len(result) == 1
    mock_database.query.assert_called()
```

## Parametrization: Advanced Techniques

### Multiple Parameters with IDs

```python
@pytest.mark.parametrize(
    "username,password,expected_status",
    [
        ("admin", "correct", 200),
        ("admin", "wrong", 401),
        ("", "password", 422),
    ],
    ids=["valid_login", "wrong_password", "missing_username"]
)
def test_login(username, password, expected_status):
    response = login(username, password)
    assert response.status_code == expected_status
```

Run with `-v` to see IDs:
```
test_login[valid_login] PASSED
test_login[wrong_password] PASSED
test_login[missing_username] PASSED
```

### Parametrizing Fixtures

```python
@pytest.fixture(params=["sqlite", "postgresql"])
def database(request):
    db_type = request.param
    if db_type == "sqlite":
        return setup_sqlite()
    else:
        return setup_postgresql()

def test_query(database):
    # Runs twice: once with SQLite, once with PostgreSQL
    result = database.query("SELECT 1")
    assert result is not None
```

### Indirect Parametrization

```python
@pytest.fixture
def user(request):
    return {"id": request.param, "name": "Test User"}

@pytest.mark.parametrize("user", [1, 2, 3], indirect=True)
def test_user_ids(user):
    # Runs three times with different user IDs
    assert user["id"] in [1, 2, 3]
```

## Custom Marks

### Creating and Using Marks

```python
import pytest

pytestmark = pytest.mark.slow

@pytest.mark.slow
def test_slow_operation():
    # This is a slow test
    pass

@pytest.mark.fast
def test_fast_operation():
    # This is a fast test
    pass
```

Run only fast tests:
```bash
pytest -m fast
```

### Conditional Skipping

```python
import sys

@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9+")
def test_new_feature():
    pass

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.xfail(reason="Known bug")
def test_known_issue():
    assert False  # Expected to fail
```

## Spying on Functions

### Using Mock.call_args

```python
from unittest.mock import call

@patch("app.send_email")
def test_email_calls(mock_send):
    send_notifications(["alice@example.com", "bob@example.com"])

    # Verify multiple calls
    assert mock_send.call_count == 2
    mock_send.assert_has_calls([
        call("alice@example.com"),
        call("bob@example.com"),
    ])
```

### Tracking Call Arguments

```python
@patch("app.logger.info")
def test_logging(mock_log):
    process_user(user_id=123)

    # Get the call arguments
    args, kwargs = mock_log.call_args
    assert "123" in str(args[0])
```

## Fixtures with Request Context

### Access Test Metadata

```python
@pytest.fixture
def test_info(request):
    return {
        "test_name": request.node.name,
        "test_file": request.node.fspath,
        "test_class": request.cls.__name__ if request.cls else None,
    }

def test_with_metadata(test_info):
    assert test_info["test_name"] == "test_with_metadata"
```

### Parameterized Fixture Teardown

```python
@pytest.fixture(params=[1, 2, 3])
def resource(request):
    print(f"Setup for param {request.param}")
    yield f"resource-{request.param}"
    print(f"Cleanup for param {request.param}")

def test_resource(resource):
    assert resource.startswith("resource-")
```

## Performance Testing

### Using pytest-benchmark

```python
def test_performance(benchmark):
    result = benchmark(expensive_function)
    assert result is not None
```

Run with:
```bash
pytest --benchmark-only
```

### Timeout Testing

```python
import pytest

@pytest.mark.timeout(1)  # Requires pytest-timeout
def test_must_complete_quickly():
    result = quick_operation()
    assert result is not None

@pytest.mark.timeout(5)
def test_longer_operation():
    result = slower_operation()
    assert result is not None
```

Install: `pip install pytest-timeout`

## Fixture Dependencies

### Fixtures Depending on Fixtures

```python
@pytest.fixture
def user_data():
    return {"name": "Alice", "email": "alice@example.com"}

@pytest.fixture
def user_in_db(user_data, database):
    user = database.create_user(user_data)
    yield user
    database.delete_user(user.id)

def test_user_in_db(user_in_db):
    assert user_in_db.name == "Alice"
```

### Dynamic Fixture Dependencies

```python
@pytest.fixture
def config(request):
    env = request.getfixturevalue("environment")
    return load_config(env)

@pytest.fixture
def environment():
    return "test"

def test_config(config):
    assert config is not None
```

## Reporting and Debugging

### Custom Assertions

```python
def assert_valid_user(user):
    assert user is not None, "User is None"
    assert hasattr(user, "id"), "User missing id"
    assert hasattr(user, "email"), "User missing email"
    assert "@" in user.email, f"Invalid email: {user.email}"

def test_user_validity(user):
    assert_valid_user(user)
```

### Capturing Output

```python
def test_with_output(capsys):
    print("Hello, World!")
    captured = capsys.readouterr()
    assert "Hello" in captured.out

def test_with_logging(caplog):
    logger.info("Test message")
    assert "Test message" in caplog.text
```

## Integration Testing

### Multi-Layer Testing

```python
@pytest.fixture
def full_app_stack():
    # Start database
    db = setup_test_db()
    # Start app
    app = create_app(db)
    client = TestClient(app)

    yield client

    # Cleanup
    teardown_test_db(db)

def test_full_workflow(full_app_stack):
    # Create user
    response = full_app_stack.post("/users/", json={"name": "Test"})
    user_id = response.json()["id"]

    # Retrieve user
    response = full_app_stack.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test"
```
