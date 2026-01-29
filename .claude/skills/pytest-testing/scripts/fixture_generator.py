#!/usr/bin/env python3
"""
Fixture generator utility for creating common pytest fixture patterns.

Usage:
    python fixture_generator.py --fixture-type factory --name user
    python fixture_generator.py --fixture-type database --name postgres
"""

import argparse
import sys
from typing import Dict, Any


FIXTURE_TEMPLATES = {
    "factory": """@pytest.fixture
def {name}_factory():
    \"\"\"Factory for creating {name} objects with customizable data\"\"\"
    def _make_{name}(**kwargs) -> dict:
        return {{
            # Add fields here
            **kwargs,
        }}
    return _make_{name}
""",

    "database": """@pytest.fixture
def {name}_connection(test_config):
    \"\"\"Create {name} connection for testing\"\"\"
    # Initialize connection
    connection = connect_to_{name}(test_config)
    yield connection
    # Cleanup
    connection.close()
""",

    "mock": """@pytest.fixture
def mock_{name}():
    \"\"\"Mock {name} service\"\"\"
    from unittest.mock import patch, MagicMock

    with patch("app.{name}") as mock:
        mock.some_method.return_value = {{"status": "mocked"}}
        yield mock
""",

    "data": """@pytest.fixture
def {name}_data():
    \"\"\"Sample {name} data for tests\"\"\"
    return {{
        "id": 1,
        "name": "{name}_test",
    }}
""",

    "async": """@pytest.fixture
async def {name}_async():
    \"\"\"Async fixture for {name}\"\"\"
    # Setup
    resource = await setup_{name}()
    yield resource
    # Cleanup
    await cleanup_{name}(resource)
""",

    "autouse": """@pytest.fixture(autouse=True)
def {name}_autouse():
    \"\"\"Auto-run fixture for {name} setup/teardown\"\"\"
    # Setup runs before each test
    yield
    # Cleanup runs after each test
""",

    "parametrized": """@pytest.fixture(params={params})
def {name}_parametrized(request):
    \"\"\"Parametrized fixture for {name} with multiple values\"\"\"
    return request.param
""",

    "scoped": """@pytest.fixture(scope="{scope}")
def {name}_{scope}():
    \"\"\"Scoped fixture for {name} ({scope} level)\"\"\"
    yield {{}}
""",
}


class FixtureGenerator:
    """Generate pytest fixture code"""

    def generate(self, fixture_type: str, name: str, **kwargs) -> str:
        """Generate fixture code for given type and name"""
        if fixture_type not in FIXTURE_TEMPLATES:
            raise ValueError(
                f"Unknown fixture type: {fixture_type}. "
                f"Available: {', '.join(FIXTURE_TEMPLATES.keys())}"
            )

        template = FIXTURE_TEMPLATES[fixture_type]
        return template.format(name=name, **kwargs)

    def generate_conftest(self, fixtures: Dict[str, Dict[str, Any]]) -> str:
        """Generate complete conftest.py from fixture definitions"""
        lines = [
            '"""Auto-generated conftest.py with pytest fixtures"""',
            "",
            "import pytest",
            "",
            "",
        ]

        for fixture_type, config in fixtures.items():
            name = config.get("name", fixture_type)
            fixture_code = self.generate(fixture_type, name, **config)
            lines.append(fixture_code)
            lines.append("")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate pytest fixture code"
    )
    parser.add_argument(
        "--fixture-type",
        choices=list(FIXTURE_TEMPLATES.keys()),
        required=True,
        help="Type of fixture to generate",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Name for the fixture",
    )
    parser.add_argument(
        "--scope",
        default="function",
        help="Fixture scope (for scoped fixtures)",
    )
    parser.add_argument(
        "--params",
        default="['value1', 'value2']",
        help="Parameters (for parametrized fixtures)",
    )

    args = parser.parse_args()

    generator = FixtureGenerator()

    kwargs = {}
    if args.fixture_type == "scoped":
        kwargs["scope"] = args.scope
    elif args.fixture_type == "parametrized":
        kwargs["params"] = args.params

    try:
        code = generator.generate(args.fixture_type, args.name, **kwargs)
        print(code)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
