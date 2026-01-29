# Test Organization and Project Structure

## Project Directory Layout

### Recommended Structure

```
my_project/
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── services.py
│   └── api.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_api.py
│   ├── unit/                    # Unit tests
│   │   ├── conftest.py
│   │   ├── test_parsing.py
│   │   └── test_validation.py
│   ├── integration/             # Integration tests
│   │   ├── conftest.py
│   │   ├── test_database.py
│   │   └── test_api_endpoints.py
│   └── fixtures/                # Shared test data
│       ├── users.json
│       └── products.json
├── pytest.ini                   # Pytest configuration
└── pyproject.toml               # Project metadata
```

### pytest.ini Configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Organizing Tests by Layer

### Unit Tests (No External Dependencies)

```python
# tests/unit/test_validation.py
class TestEmailValidation:
    def test_valid_email(self):
        assert is_valid_email("user@example.com")

    def test_invalid_email_no_at(self):
        assert not is_valid_email("userexample.com")

    def test_invalid_email_empty(self):
        assert not is_valid_email("")
```

Run only unit tests:
```bash
pytest tests/unit/
```

### Integration Tests (With External Dependencies)

```python
# tests/integration/test_database.py
@pytest.mark.integration
class TestUserRepository:
    @pytest.fixture
    def db(self):
        connection = setup_test_db()
        yield connection
        teardown_test_db(connection)

    def test_create_and_retrieve_user(self, db):
        user = db.create_user({"name": "Alice"})
        retrieved = db.get_user(user.id)
        assert retrieved.name == "Alice"

    def test_update_user(self, db):
        user = db.create_user({"name": "Bob"})
        db.update_user(user.id, {"name": "Bob Updated"})
        retrieved = db.get_user(user.id)
        assert retrieved.name == "Bob Updated"
```

Run only integration tests:
```bash
pytest -m integration
```

### End-to-End Tests (Full Application)

```python
# tests/e2e/test_workflows.py
@pytest.mark.e2e
class TestUserWorkflow:
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)

    def test_register_and_login_workflow(self, client):
        # Register
        response = client.post("/auth/register/", json={
            "email": "new@example.com",
            "password": "secure123"
        })
        assert response.status_code == 201

        # Login
        response = client.post("/auth/login/", json={
            "email": "new@example.com",
            "password": "secure123"
        })
        assert response.status_code == 200
        token = response.json()["token"]

        # Access protected endpoint
        response = client.get(
            "/user/profile/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
```

## conftest.py: Sharing Fixtures

### Root conftest.py (Shared Across All Tests)

```python
# tests/conftest.py
import pytest
from app import create_app

@pytest.fixture(scope="session")
def app():
    """Create test app once per session"""
    return create_app(config="test")

@pytest.fixture
def client(app):
    """Provide TestClient for each test"""
    return TestClient(app)

@pytest.fixture
def sample_user():
    """Standard test user"""
    return {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User"
    }
```

### Layer-Specific conftest.py (Unit Tests)

```python
# tests/unit/conftest.py
import pytest

@pytest.fixture
def mock_database():
    """Mock database for unit tests"""
    with patch("app.database") as mock:
        yield mock
```

### Layer-Specific conftest.py (Integration Tests)

```python
# tests/integration/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine

@pytest.fixture
def db_session(test_db):
    """Provide clean database session per test"""
    connection = test_db.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

## Fixture Discovery and Scope

### Fixture Lookup Order

1. Test file local fixtures
2. `conftest.py` in same directory
3. `conftest.py` in parent directories (up to root)
4. Plugins

Example:
```
tests/
├── conftest.py                  # Available to all tests
│   @pytest.fixture
│   def app():
├── unit/
│   ├── conftest.py              # Available to unit tests only
│   │   @pytest.fixture
│   │   def mock_service():
│   └── test_models.py
└── integration/
    ├── conftest.py              # Available to integration tests only
    │   @pytest.fixture
    │   def real_database():
    └── test_api.py
```

## Naming Conventions

### Test Files

```python
test_models.py          # Tests for models module
test_user_service.py    # Tests for user service
test_api.py             # Tests for API endpoints
```

### Test Classes

```python
class TestUserModel:        # Test the User model
class TestEmailValidation:  # Test email validation
class TestAuthAPI:          # Test auth API endpoints
```

### Test Functions

```python
def test_user_creation():           # Basic behavior
def test_user_creation_with_email():  # Specific case
def test_invalid_email_raises_error():  # Error case
def test_user_creation_empty_name():  # Edge case
```

## Managing Test Data

### Inline Fixtures (Simple Data)

```python
@pytest.fixture
def user_data():
    return {
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30
    }
```

### File-Based Fixtures (Large Datasets)

```python
# tests/fixtures/users.json
[
  {"id": 1, "name": "Alice", "email": "alice@example.com"},
  {"id": 2, "name": "Bob", "email": "bob@example.com"}
]

# tests/conftest.py
import json

@pytest.fixture
def users_data():
    with open("tests/fixtures/users.json") as f:
        return json.load(f)
```

### Factory Fixtures (Generating Variations)

```python
@pytest.fixture
def user_factory():
    def _create_user(name="Default", email="default@example.com", **kwargs):
        return {
            "name": name,
            "email": email,
            **kwargs
        }
    return _create_user

def test_multiple_users(user_factory):
    admin = user_factory(name="Admin", email="admin@example.com")
    user = user_factory(name="User", email="user@example.com")
    assert admin["name"] != user["name"]
```

## Running Tests Efficiently

### Run Specific Tests

```bash
pytest tests/unit/test_models.py           # Single file
pytest tests/unit/test_models.py::TestUser  # Single class
pytest tests/unit/test_models.py::TestUser::test_creation  # Single test
```

### Filter by Markers

```bash
pytest -m "not slow"                       # Skip slow tests
pytest -m "integration"                    # Only integration tests
pytest -m "unit and not slow"              # Combinations
```

### Filter by Name Pattern

```bash
pytest -k "email"                          # Tests with "email" in name
pytest -k "not slow"                       # Exclude "slow" from name
pytest -k "test_user and not deletion"     # Complex patterns
```

### Parallel Execution

```bash
# Install: pip install pytest-xdist
pytest -n auto                             # Use all CPU cores
pytest -n 4                                # Use 4 workers
```

## Debugging Test Failures

### Verbose Output

```bash
pytest -v                                  # Show all tests
pytest -vv                                 # More details
pytest --tb=long                           # Full traceback
pytest --tb=no                             # No traceback
```

### Stop on First Failure

```bash
pytest -x                                  # Stop on first failure
pytest --lf                                # Run last failed tests
pytest --ff                                # Run failed first, then others
```

### Print Debug Output

```python
def test_with_debug(capsys):
    print("Debug info")
    captured = capsys.readouterr()
    assert "Debug" in captured.out

# Run with:
# pytest -s  (or --capture=no)
```

### Interactive Debugging

```python
import pdb

def test_with_breakpoint():
    result = complex_calculation()
    pdb.set_trace()  # Debugger stops here
    assert result > 0
```

Run with `pytest --pdb` to start debugger on failure.
