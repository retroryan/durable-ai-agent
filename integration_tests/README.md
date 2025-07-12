# Integration Tests

This directory contains two types of integration tests for the durable AI agent:

1. **API Integration Tests** (pytest-based) - Test API endpoints with HTTP requests
2. **MCP Integration Tests** (direct Python programs) - Test MCP client functionality

## MCP Integration Tests

The MCP integration tests are **direct Python programs (not pytest)** to avoid complexity and issues with async test runners and connection pooling. **We want to keep it this way** because:

1. Complex async handling and event loop conflicts with MCP clients
2. Connection pooling issues when running multiple tests
3. Fixture lifecycle conflicts with long-lived connections
4. Simpler debugging and error messages
5. Direct control over test execution and cleanup

### Running MCP Tests

```bash
# Run all MCP integration tests including HTTP (requires MCP HTTP server on port 7778)
python mcp_servers/forecast_server.py  # In one terminal
python integration_tests/run_integration_tests.py  # In another terminal

# Run tests without HTTP tests
python integration_tests/run_integration_tests.py --no-http

# Run individual tests directly
python integration_tests/test_stdio_client.py
python integration_tests/test_http_client.py  # Requires server on port 7778
```

Each MCP test loads the `.env` file independently and uses environment variables for configuration.

## API Integration Tests

The API integration tests use pytest and test the API server with actual HTTP requests.

### Prerequisites

1. The API server must be running before running these tests
2. Temporal must be running
3. The worker must be running

### Setup

1. Start the services (from the project root):
   ```bash
   docker-compose up
   ```

2. Or run services locally:
   ```bash
   # Terminal 1: Start Temporal
   temporal server start-dev
   
   # Terminal 2: Start the worker
   poetry run python worker/main.py
   
   # Terminal 3: Start the API
   poetry run python -m api.main
   ```

### Running API Tests

From the project root:

```bash
# Run all API integration tests
poetry run pytest integration_tests/ -v

# Run only API endpoint tests
poetry run pytest integration_tests/test_api_endpoints.py -v

# Run only workflow tests
poetry run pytest integration_tests/test_workflow_integration.py -v

# Run tests with specific markers
poetry run pytest integration_tests/ -m api -v
poetry run pytest integration_tests/ -m workflow -v

# Run with custom API URL
API_URL=http://localhost:8001 poetry run pytest integration_tests/ -v
```

## Test Structure

### API Tests (pytest-based)
- `conftest.py` - Pytest configuration and fixtures
- `utils/` - Test utilities
  - `api_client.py` - HTTP client wrapper for API calls
  - `test_helpers.py` - Assertion helpers and utilities
- `test_api_endpoints.py` - Tests for API endpoints
- `test_workflow_integration.py` - Tests for workflow functionality

### MCP Tests (direct Python programs)
- `test_stdio_client.py` - Test stdio MCP client connection
- `test_http_client.py` - Test HTTP MCP client connection
- `run_integration_tests.py` - Run all MCP tests

## Environment Configuration

All tests load configuration from the `.env` file in the project root. Key variables:

```bash
# API Configuration
API_URL=http://localhost:8000

# MCP Server Configuration
MCP_FORECAST_SERVER_HOST=localhost
MCP_FORECAST_SERVER_PORT=7778
MCP_FORECAST_SERVER_URL=http://localhost:7778/mcp
```

## Test Categories

API tests are marked with the following markers:
- `@pytest.mark.api` - Tests that require the API server
- `@pytest.mark.workflow` - Tests for workflow functionality
- `@pytest.mark.slow` - Tests that take longer to run

## Writing New Tests

### API Tests (pytest)
1. Use the `api_client` fixture to make API calls
2. Use `WorkflowAssertions` for common assertions
3. Mark tests appropriately with `@pytest.mark.api` or `@pytest.mark.workflow`
4. Use `async def` for all test functions

Example:
```python
@pytest.mark.api
@pytest.mark.asyncio
async def test_my_feature(api_client):
    response = await api_client.chat("Test message")
    WorkflowAssertions.assert_workflow_completed(response)
```

### MCP Tests (direct Python)
1. Load `.env` file at the start of each test
2. Use direct async/await without pytest fixtures
3. Handle cleanup explicitly
4. Make the file executable with `#!/usr/bin/env python3`

Example:
```python
#!/usr/bin/env python3
"""Simple MCP test.

This is a direct Python program (not pytest) to avoid complexity and issues
with async test runners and connection pooling.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

async def test_my_mcp_feature():
    # Your test code here
    pass

if __name__ == "__main__":
    exit_code = asyncio.run(test_my_mcp_feature())
    sys.exit(exit_code)
```

## Debugging

### API Tests
If tests fail with connection errors:
1. Check that all services are running
2. Check the API_URL environment variable
3. Check service logs for errors
4. Verify Temporal UI at http://localhost:8080

### MCP Tests
If MCP tests fail:
1. Check that the MCP server is running (for HTTP tests)
2. Check the MCP server configuration in `.env`
3. Run tests individually for better error messages
4. Check that the forecast server script is executable