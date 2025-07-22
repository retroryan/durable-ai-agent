# Integration Tests

This directory contains integration tests for the Durable AI Agent project. The test suite has been simplified to focus on two distinct types of testing:

1. **MCP Connection Tests** - Test MCP server connections (STDIO and HTTP)
2. **API E2E Tests** - Test complete workflows through the API

## Test Philosophy

All tests are **direct Python programs (not pytest)** to maintain simplicity and avoid complexity with async test runners and connection pooling. This approach provides:
- Simple, readable test code
- Direct control over execution
- Clear error messages
- No hidden magic or complex frameworks

## Test Structure

```
integration_tests/
├── test_mcp_connections.py  # Tests STDIO and HTTP connections to MCP servers
├── test_api_e2e.py         # Tests complete workflows through the API
└── run_integration_tests.py # Test runner for all tests
```

## Running the Tests

### Prerequisites

- Python environment with Poetry installed
- Project dependencies installed: `poetry install`
- `.env` file configured (copy from `.env.example` if needed)

### Mode 1: MCP Connection Tests (Local)

These tests verify that MCP servers can be accessed via HTTP connections.

```bash
# Start all MCP servers locally
poetry run python scripts/run_mcp_servers.py

# In another terminal, run the connection tests
poetry run python integration_tests/test_mcp_connections.py

# Optionally test STDIO connection as well
poetry run python integration_tests/test_mcp_connections.py --stdio

# When done, stop the MCP servers
poetry run python scripts/stop_mcp_servers.py
```

The test will:
- Test HTTP connections to all three MCP servers (forecast, historical, agricultural)
- Verify each server's tools can be listed and invoked
- Optionally test STDIO connection if --stdio flag is provided
- Display clear pass/fail results for each server

### Mode 2: API E2E Tests (Docker Compose)

These tests verify complete workflows through the API, including tool selection and execution.

```bash
# Make sure MCP servers are stopped first
poetry run python scripts/stop_mcp_servers.py

# Start all services with docker-compose
docker-compose up -d

# Or with weather proxy profile
docker-compose --profile weather_proxy up -d

# Run the E2E tests
poetry run python integration_tests/test_api_e2e.py

# When done, stop docker-compose
docker-compose down
```

## Environment Configuration

The tests use environment variables from `.env`:

```bash
# MCP Server Configuration
MCP_FORECAST_SERVER_HOST=localhost
MCP_FORECAST_SERVER_PORT=7778
MCP_FORECAST_SERVER_URL=http://localhost:7778/mcp

# API Configuration (for E2E tests)
API_URL=http://localhost:8000
```

## Test Details

### test_mcp_connections.py

Tests HTTP connections to all MCP servers (and optionally STDIO):
- **HTTP Tests**: Connects to all three running MCP servers (forecast, historical, agricultural)
- **STDIO Test**: Only runs with --stdio flag, launches forecast server as subprocess

Output example:
```
=== Testing Forecast Server (HTTP) ===
URL: http://localhost:7778/mcp
✓ Connected to server
✓ Found 1 tools
   - get_weather_forecast
✓ Tool invocation successful, got response with 5 keys
✓ Forecast server test passed!

=== Testing Historical Server (HTTP) ===
URL: http://localhost:7779/mcp
✓ Connected to server
✓ Found 1 tools
   - get_historical_weather
✓ Tool invocation successful, got response with 4 keys
✓ Historical server test passed!

=== Testing Agricultural Server (HTTP) ===
URL: http://localhost:7780/mcp
✓ Connected to server
✓ Found 1 tools
   - get_agricultural_conditions
✓ Tool invocation successful, got response with 6 keys
✓ Agricultural server test passed!

SUMMARY
Total tests run: 3
Passed: 3
Failed: 0
```

### test_api_e2e.py

Tests complete workflows through the API:
- Sends weather-related queries
- Verifies tool selection and execution
- Checks response quality
- Tests multiple tool scenarios

## Troubleshooting

### MCP Connection Tests Failing

1. **STDIO Test Fails**:
   - Check that `mcp_servers/forecast_server.py` exists
   - Verify Python can run the server script
   - Check for Python path issues

2. **HTTP Test Fails**:
   - Ensure MCP servers are running: `poetry run python scripts/run_mcp_servers.py`
   - Check that ports 7778-7780 are not in use
   - Verify the server URLs in `.env`

### API E2E Tests Failing

1. **Connection Refused**:
   - Ensure docker-compose is running: `docker-compose ps`
   - Check that the API is healthy: `curl http://localhost:8000/health`
   - Verify Temporal UI is accessible at http://localhost:8080

2. **Workflow Errors**:
   - Check worker logs: `docker-compose logs worker`
   - Verify MCP proxy is running: `docker-compose logs weather-proxy`
   - Check for any Python errors in the logs

## Adding New Tests

Keep tests simple and focused:

```python
#!/usr/bin/env python3
"""Test description here."""
import asyncio

async def test_something():
    """Test specific functionality."""
    print("Testing something...")
    # Test logic here
    print("✓ Test passed!")
    return True

async def main():
    if await test_something():
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

## Important Notes

- Always stop local MCP servers before starting docker-compose to avoid port conflicts
- Tests are designed to be run independently, not as part of a test suite
- Each test provides clear console output for easy debugging
- No complex test frameworks or fixtures - just simple Python scripts