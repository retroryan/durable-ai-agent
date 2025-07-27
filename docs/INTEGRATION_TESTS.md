# Integration Tests

This directory contains integration tests for the Durable AI Agent project. The test suite has been simplified to focus on two distinct types of testing:

1. **MCP Connection Tests** - Test MCP server connections via HTTP
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

These tests verify that the MCP server can be accessed via HTTP connection.

```bash
# Start the MCP server locally
poetry run python scripts/run_mcp_server.py

# In another terminal, run the connection tests
poetry run python integration_tests/test_mcp_connections.py

# When done, stop the MCP server
poetry run python scripts/stop_mcp_server.py
```

The test will:
- Test HTTP connection to the MCP server on port 7778
- Verify all three tools (forecast, historical, agricultural) are available
- Test invocation of each tool
- Display clear pass/fail results for each tool

### Mode 2: API E2E Tests (Docker Compose)

These tests verify complete workflows through the API, including tool selection and execution.

```bash
# Make sure MCP server is stopped first
poetry run python scripts/stop_mcp_server.py

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
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=7778
MCP_SERVER_URL=http://localhost:7778/mcp

# API Configuration (for E2E tests)
API_URL=http://localhost:8000
```

## Test Details

### test_mcp_connections.py

Tests HTTP connection to the MCP server:
- **HTTP Test**: Connects to the MCP server on port 7778 with all three tools
- **Tool Testing**: Invokes each of the three tools with sample data

Output example:
```
=== Testing MCP Server (HTTP) ===
URL: http://localhost:7778/mcp
✓ Connected to server
✓ Found 3 tools:
   - get_weather_forecast
   - get_historical_weather
   - get_agricultural_conditions

Testing get_weather_forecast:
✓ Tool invocation successful, got response with 5 keys

Testing get_historical_weather:
✓ Tool invocation successful, got response with 4 keys

Testing get_agricultural_conditions:
✓ Tool invocation successful, got response with 6 keys

✓ MCP server test passed!

SUMMARY
Total tools tested: 3
All tests passed!
```

### test_api_e2e.py

Tests complete workflows through the API:
- Sends weather-related queries
- Verifies tool selection and execution
- Checks response quality
- Tests multiple tool scenarios

## Troubleshooting

### MCP Connection Tests Failing

1. **HTTP Test Fails**:
   - Ensure MCP server is running: `poetry run python scripts/run_mcp_server.py`
   - Check that port 7778 is not in use: `lsof -i :7778`
   - Verify the server URL in `.env`
   - Check server health: `curl http://localhost:7778/health`

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