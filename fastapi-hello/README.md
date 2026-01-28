# FastAPI Hello World

A simple FastAPI project demonstrating a basic "Hello World" application with multiple endpoints using the `uv` package manager.

## Prerequisites

- Python 3.10 or higher
- `uv` package manager ([install uv](https://docs.astral.sh/uv/getting-started/installation/))

## Installation

### 1. Install uv (if not already installed)

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone or navigate to the project

```bash
cd fastapi-hello
```

### 3. Install dependencies

Using `uv`, dependencies are automatically managed from `pyproject.toml`:

```bash
uv sync
```

This command will:
- Create a virtual environment (if needed)
- Install FastAPI and Uvicorn
- Generate a `uv.lock` file for reproducible builds

## Running the Application

### Start the FastAPI server

```bash
uv run fastapi dev main.py
```

Or if you prefer using Uvicorn directly:

```bash
uv run uvicorn main.py:app --reload
```

The server will start at `http://localhost:8000`

## Hello World Endpoints

Once the server is running, you can test the following endpoints:

### 1. Root Endpoint

```bash
curl http://localhost:8000/
```

Response:
```json
{"message": "Hello, World!"}
```

### 2. Dynamic Greeting Endpoint

```bash
curl http://localhost:8000/hello/Alice
```

Response:
```json
{"message": "Hello, Alice!"}
```

## Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Visit these URLs in your browser to explore and test the endpoints interactively.

## Project Structure

```
fastapi-hello/
├── main.py              # FastAPI application with endpoints
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Locked dependency versions (generated)
├── .python-version     # Python version specification
└── README.md           # This file
```

## Available Commands

```bash
# Install dependencies
uv sync

# Run the development server with auto-reload
uv run fastapi dev main.py

# Run with Uvicorn directly
uv run uvicorn main.py:app --reload

# Run without auto-reload
uv run uvicorn main.py:app

# Add a new dependency
uv add package-name

# Remove a dependency
uv remove package-name

# Update dependencies
uv sync --upgrade
```

## Dependencies

- **FastAPI** (>=0.128.0): Modern web framework for building APIs
- **Uvicorn** (>=0.40.0): ASGI server for running the application

## Tips

- The `--reload` flag enables auto-reload when you modify `main.py`
- FastAPI provides automatic request validation and serialization
- The interactive docs at `/docs` is great for testing during development
- Use `Ctrl+C` to stop the server

## Next Steps

- Add more endpoints to `main.py`
- Add request/response models using Pydantic
- Add authentication and authorization
- Deploy to production using Docker or cloud platforms

## Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [uv Documentation](https://docs.astral.sh/uv/)
