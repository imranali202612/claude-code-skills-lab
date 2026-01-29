"""
Reusable conftest template for new pytest projects.

This file demonstrates common fixture patterns. Copy and customize for your project.
Place in your tests/ directory as conftest.py
"""

import pytest
from typing import Generator


# ============================================================================
# SESSION-LEVEL FIXTURES (Shared across entire test suite)
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Load test configuration once per session"""
    return {
        "database_url": "sqlite:///:memory:",
        "debug": True,
        "timeout": 30,
    }


# ============================================================================
# MODULE-LEVEL FIXTURES (Shared within a test file)
# ============================================================================

@pytest.fixture(scope="module")
def test_database(test_config) -> Generator:
    """Create test database once per module, clean up after"""
    from sqlalchemy import create_engine

    engine = create_engine(test_config["database_url"])
    # Create tables
    # Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    # Base.metadata.drop_all(engine)


# ============================================================================
# FUNCTION-LEVEL FIXTURES (Fresh for each test)
# ============================================================================

@pytest.fixture
def db_session(test_database) -> Generator:
    """Provide clean database session with rollback after each test"""
    from sqlalchemy.orm import sessionmaker

    connection = test_database.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def app():
    """Create application instance for testing"""
    from app import create_app
    return create_app(config="test")


@pytest.fixture
def client(app):
    """Provide FastAPI TestClient"""
    from fastapi.testclient import TestClient
    return TestClient(app)


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_user_data():
    """Standard user data for tests"""
    return {
        "id": 1,
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
    }


@pytest.fixture
def sample_product_data():
    """Standard product data for tests"""
    return {
        "id": 1,
        "name": "Test Product",
        "price": 99.99,
        "in_stock": True,
    }


# ============================================================================
# FACTORY FIXTURES (Generate multiple test objects)
# ============================================================================

@pytest.fixture
def user_factory():
    """Factory for creating user objects with customizable data"""
    def _make_user(
        email: str = "user@example.com",
        name: str = "Test User",
        is_active: bool = True,
        **kwargs
    ) -> dict:
        return {
            "email": email,
            "name": name,
            "is_active": is_active,
            **kwargs,
        }
    return _make_user


@pytest.fixture
def product_factory():
    """Factory for creating product objects"""
    def _make_product(
        name: str = "Product",
        price: float = 99.99,
        in_stock: bool = True,
        **kwargs
    ) -> dict:
        return {
            "name": name,
            "price": price,
            "in_stock": in_stock,
            **kwargs,
        }
    return _make_product


# ============================================================================
# MOCKING FIXTURES
# ============================================================================

@pytest.fixture
def mock_external_api():
    """Mock external API calls"""
    from unittest.mock import patch, MagicMock

    with patch("app.external_api") as mock:
        mock.get_data.return_value = {"status": "success"}
        yield mock


@pytest.fixture
def mock_email_service():
    """Mock email service"""
    from unittest.mock import patch

    with patch("app.send_email") as mock:
        mock.return_value = True
        yield mock


# ============================================================================
# AUTOUSE FIXTURES (Run automatically for all tests)
# ============================================================================

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset test environment before each test"""
    # Clear caches
    # Reset global state
    yield
    # Cleanup after test


@pytest.fixture(autouse=True)
def suppress_warnings():
    """Suppress expected warnings during tests"""
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        yield


# ============================================================================
# PARAMETRIZED FIXTURE
# ============================================================================

@pytest.fixture(params=["test", "development"])
def environment(request):
    """Parametrized fixture that runs each test in different environments"""
    return request.param


# ============================================================================
# REQUEST CONTEXT FIXTURE
# ============================================================================

@pytest.fixture
def test_metadata(request):
    """Provide metadata about current test"""
    return {
        "test_name": request.node.name,
        "test_file": str(request.node.fspath),
        "test_class": request.cls.__name__ if request.cls else None,
        "test_markers": [marker.name for marker in request.node.iter_markers()],
    }


# ============================================================================
# DEPENDENCY OVERRIDE FOR FASTAPI
# ============================================================================

@pytest.fixture
def client_with_auth(app, sample_user_data):
    """FastAPI client with mocked authentication"""
    from fastapi.testclient import TestClient
    from unittest.mock import patch

    def override_get_current_user():
        return sample_user_data

    # Assuming your app has a get_current_user dependency
    # app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    yield client

    # Cleanup
    # app.dependency_overrides.clear()


# ============================================================================
# FIXTURE FOR CAPTURING OUTPUT
# ============================================================================

@pytest.fixture
def capture_logs(caplog):
    """Capture and return logs from test execution"""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


# ============================================================================
# TIPS FOR CUSTOM FIXTURES
# ============================================================================
"""
1. USE APPROPRIATE SCOPE
   - function (default): Fresh per test, good isolation
   - class: Shared by test class methods
   - module: Shared across all tests in a file
   - session: Shared across entire run (use carefully)

2. FIXTURE DEPENDENCIES
   Fixtures can depend on other fixtures:
   @pytest.fixture
   def derived_fixture(base_fixture):
       return transform(base_fixture)

3. PARAMETRIZATION
   Run each test with different fixture values:
   @pytest.fixture(params=["value1", "value2"])
   def my_fixture(request):
       return request.param

4. CLEANUP WITH YIELD
   Code after yield runs after test:
   @pytest.fixture
   def resource():
       setup()
       yield resource
       cleanup()

5. REQUEST INTROSPECTION
   Access test metadata:
   @pytest.fixture
   def my_fixture(request):
       test_name = request.node.name
       markers = request.node.iter_markers()

6. CONDITIONAL FIXTURES
   Return different values based on conditions:
   @pytest.fixture
   def env_fixture(request):
       if "slow" in request.node.keywords:
           return slow_setup()
       return fast_setup()
"""
