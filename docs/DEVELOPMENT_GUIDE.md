# Development Guide

This guide covers all aspects of developing, testing, and running the Durable AI Agent project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [MCP Server Development](#mcp-server-development)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Project Structure](#project-structure)
- [Docker Development](#docker-development)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose
- Python 3.10+ with Poetry
- Node.js 20+ (for frontend)
- Temporal CLI (for local development)

## Development Setup

### Initial Setup

```bash
# Install Python dependencies
poetry install

# Set up environment files
cp .env.example .env

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Environment Configuration

The `.env` file contains all configuration for the project:

```bash
# LLM Configuration
ANTHROPIC_API_KEY=your-api-key-here

# MCP Server Configuration
MCP_FORECAST_SERVER_URL=http://localhost:7778/mcp

# Additional servers...
```

## MCP Server Development

The project uses a unified MCP server architecture with all weather tools consolidated into a single server.

### Server Architecture

```
mcp_servers/
├── agricultural_server.py    # Main unified server (all tools)
├── utils/
│   ├── weather_utils.py     # Core implementation logic
│   └── api_client.py        # OpenMeteo API client
├── mock_weather_utils.py    # Mock data for testing
└── sample_pydantic_client.py # Example client implementation
```

### Running MCP Server

```bash
# Start the MCP server
poetry run python scripts/run_mcp_server.py

# Stop the server
poetry run python scripts/stop_mcp_server.py
```

The server runs on port 7778 and exposes all three tools.

### Available Tools

1. **get_weather_forecast** - Real-time and predictive weather data
2. **get_historical_weather** - Historical weather patterns and trends
3. **get_agricultural_conditions** - Farm-specific conditions and growing data

All tools use Pydantic models for type safety and validation, supporting both string and numeric coordinates for AWS Bedrock compatibility.

### Adding New MCP Tools

1. Define the Pydantic model in `models/mcp_models.py`
2. Add the implementation in `mcp_servers/utils/weather_utils.py`
3. Expose via `@server.tool` decorator in `agricultural_server.py`
4. Update tests and documentation

## Running the Application

### Option 1: Full Docker Compose (Recommended)

```bash
# Start all services
./run_docker.sh

# Or manually
docker-compose up

# With specific profile
docker-compose --profile forecast up
```

### Option 2: Local Development Mode

Running Temporal and Workers in Docker-Compose with API Server and Frontend locally:

```bash
# Terminal 1: Start Temporal
temporal server start-dev

# Terminal 2: Start Worker
poetry run python scripts/run_worker.py

# Terminal 3: Start API Server
poetry run python api/main.py

# Terminal 4: Start Frontend
cd frontend && npm run dev
```

### Service URLs

- Frontend: http://localhost:3000
- API Server: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Temporal UI: http://localhost:8080
- MCP Server: http://localhost:7778/mcp

## Testing

The project uses a two-tier testing strategy:
1. **Unit Tests** - pytest-based tests for individual components
2. **Integration Tests** - Standalone Python scripts for end-to-end testing

### Running Unit Tests

```bash
# Run all unit tests
poetry run pytest

# Or use the poe task
poetry run poe test

# Run specific test categories
poetry run pytest -m api        # API tests only
poetry run pytest -m workflow   # Workflow tests only
poetry run pytest -k test_name  # Specific test by name

# Run with coverage
poetry run pytest --cov=. --cov-report=html
```

#### Environment Variable Considerations

The project uses `MCP_SERVER_URL` environment variable to configure MCP server endpoints. During testing:

- The `.env` file sets `MCP_SERVER_URL=http://mcp-server:7778/mcp` for Docker environments
- Unit tests expect the default value `http://localhost:7778/mcp` when this variable is not set
- A `conftest.py` fixture automatically removes `MCP_SERVER_URL` from the environment during tests
- This ensures tests use the expected localhost URL rather than the Docker service name

If you need to test with a specific MCP server URL, you can use pytest's environment variable patching:

```python
@patch.dict("os.environ", {"MCP_SERVER_URL": "http://custom-server:9999/mcp"})
def test_custom_mcp_url():
    # Test with custom URL
    pass
```

### Running Integration Tests

Integration tests are **standalone Python scripts** (not pytest) for simplicity and direct control.

#### MCP Connection Tests

Test MCP server connection:

```bash
# Start MCP server first
poetry run python scripts/run_mcp_server.py

# Run connection tests
poetry run python integration_tests/test_mcp_connections.py

# Stop server when done
poetry run python scripts/stop_mcp_server.py
```

For detailed integration test documentation, see [Integration Tests Guide](INTEGRATION_TESTS.md).

#### API End-to-End Tests

Test complete workflows:

```bash
# Ensure MCP servers are stopped
poetry run python scripts/stop_mcp_servers.py

# Start services with docker-compose
docker-compose up -d

# Run E2E tests
poetry run python integration_tests/test_api_e2e.py

# Stop services
docker-compose down
```

#### Running All Integration Tests

```bash
# Run all integration tests
poetry run python integration_tests/run_integration_tests.py
```

### Test Categories

- **Unit Tests** (`tests/`) - Test individual components in isolation
- **Integration Tests** (`integration_tests/`) - Test with real services
- **MCP Tests** - Test MCP server connections and tool execution
- **E2E Tests** - Test complete workflow execution through the API

### Writing Tests

#### Unit Test Example

```python
import pytest
from tools.agriculture.weather_forecast import WeatherForecastTool

@pytest.mark.asyncio
async def test_weather_forecast_tool():
    tool = WeatherForecastTool()
    result = await tool.execute(location="Chicago", days=7)
    assert "forecast" in result
    assert len(result["forecast"]) == 7
```

#### Integration Test Example

```python
#!/usr/bin/env python3
"""Test MCP server connection."""
import asyncio
from fastmcp import Client

async def test_mcp_connection():
    client = Client("http://localhost:7778/mcp")
    async with client:
        tools = await client.list_tools()
        assert len(tools) > 0
        print("✓ MCP connection test passed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
```

## Code Quality

### Linting and Formatting

```bash
# Format code
poetry run poe format

# Check code style
poetry run poe lint

# Type checking
poetry run poe lint-types

# Run all checks
poetry run poe lint
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
poetry run pre-commit install
```

### Type Hints

The project enforces type hints. Always:
- Add type annotations to function signatures
- Use Pydantic models for data validation
- Run `poetry run poe lint-types` before committing

## Project Structure

```
durable-ai-agent/
├── workflows/              # Temporal workflows
│   ├── simple_agent_workflow.py
│   └── agentic_ai_workflow.py
├── activities/             # Temporal activities
│   ├── react_agent_activity.py
│   ├── tool_execution_activity.py
│   └── extract_agent_activity.py
├── agentic_loop/          # DSPy reasoning components
│   ├── react_agent.py
│   └── extract_agent.py
├── tools/                  # Tool implementations
│   └── agriculture/       # Weather/farming tools
├── models/                 # Data models
│   ├── messages.py
│   └── mcp_models.py
├── shared/                 # Shared utilities
│   ├── tool_registry.py
│   └── mcp_client_manager.py
├── worker/                 # Temporal worker
├── api/                    # FastAPI server
├── mcp_servers/           # MCP server implementations
├── frontend/              # React UI
├── tests/                 # Unit tests
├── integration_tests/     # Integration tests
└── docker-compose.yml     # Service orchestration
```

## Docker Development

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build api-server

# Build with no cache
docker-compose build --no-cache
```

### Docker Profiles

The project uses Docker profiles for different deployment scenarios:

```bash
# Default profile (all services)
docker-compose up

# Forecast profile (with individual MCP servers)
docker-compose --profile forecast up

# Development profile
docker-compose --profile dev up
```

### Debugging Docker Services

```bash
# View logs
docker-compose logs -f [service-name]

# Execute commands in container
docker-compose exec worker bash

# Inspect container
docker inspect [container-id]
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 [PID]
```

#### MCP Server Connection Issues

1. Verify servers are running: `curl http://localhost:7778/health`
2. Check logs: `poetry run python scripts/run_mcp_servers.py`
3. Ensure `.env` has correct configuration

#### Temporal Worker Issues

1. Check worker logs: `docker-compose logs worker`
2. Verify Temporal is running: http://localhost:8080
3. Ensure workflows are registered

#### Import Errors

Always run MCP servers as modules:
```bash
# Correct
poetry run python -m mcp_servers.agricultural_server

# Incorrect (may cause import errors)
cd mcp_servers && python agricultural_server.py
```

### Debug Mode

Enable debug logging:

```bash
# For MCP servers
LOG_LEVEL=DEBUG poetry run python -m mcp_servers.agricultural_server

# For API server
LOG_LEVEL=DEBUG poetry run python api/main.py

# In docker-compose
environment:
  - LOG_LEVEL=DEBUG
```

### Performance Tips

1. **Use Coordinates**: Directly providing latitude/longitude is ~6x faster than location names
2. **Connection Pooling**: MCPClientManager reuses connections
3. **Mock Mode**: Set `MOCK_WEATHER=true` for testing without API calls
4. **Batch Operations**: Process multiple requests together when possible

## Contributing

1. Create a feature branch
2. Make your changes
3. Ensure all tests pass
4. Run code quality checks
5. Submit a pull request

See [Contributing Guide](../CONTRIBUTING.md) for detailed guidelines.