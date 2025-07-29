# Integration Tests

This directory contains integration tests for the Durable AI Agent project. The test suite focuses on verifying different aspects of the system through direct Python programs.

## Test Philosophy

All tests are **direct Python programs (not pytest)** to maintain simplicity and avoid complexity with async test runners and connection pooling. This approach provides:
- Simple, readable test code
- Direct control over execution
- Clear error messages
- No hidden magic or complex frameworks

## Test Structure

```
integration_tests/
├── test_mcp_connections.py   # Tests HTTP connections to MCP servers
├── test_api_e2e.py          # Tests complete MCP weather tool flow through API
├── test_agriculture.py      # Comprehensive agricultural tool tests with React loop visibility
├── test_multi_turn.py       # Tests multi-turn conversation capabilities
├── run_integration_tests.py # Test runner that executes MCP and API tests
└── utils/
    └── api_client.py        # Shared API client with conversation history helpers
```

## Running the Tests

### Prerequisites

- Python environment with Poetry installed
- Project dependencies installed: `poetry install`
- `.env` file configured (copy from `.env.example` if needed)
- Docker services running: `docker-compose up -d`

### Quick Start - Run All Tests

```bash
# Run the test suite (MCP + API tests)
poetry run python integration_tests/run_integration_tests.py

# Run only MCP connection tests
poetry run python integration_tests/run_integration_tests.py --mcp-only

# Run only API E2E tests
poetry run python integration_tests/run_integration_tests.py --api-only
```

### Individual Test Details

#### 1. MCP Connection Tests (`test_mcp_connections.py`)

Tests HTTP connections to the MCP server and validates all weather tools.

```bash
poetry run python integration_tests/test_mcp_connections.py
```

**What it tests:**
- Connection to MCP server on port 7778
- Lists and verifies all 3 tools are available
- Tests each tool with Pydantic models:
  - `get_weather_forecast`
  - `get_historical_weather`
  - `get_agricultural_conditions`
- Validates Pydantic model validation (coordinate conversion, error handling)
- Performance comparison (coordinates vs location names)

**Note:** Automatically handles Docker vs local hostname resolution.

#### 2. API E2E Tests (`test_api_e2e.py`)

Tests the complete MCP weather tool flow through the API.

```bash
poetry run python integration_tests/test_api_e2e.py
```

**What it tests:**
- Complete workflow execution via `/chat` endpoint
- React agent tool selection
- MCP tool execution flow
- Response quality and format
- Trajectory analysis

#### 3. Agriculture Tests (`test_agriculture.py`)

Comprehensive integration tests for agricultural use cases with detailed React loop visibility.

```bash
# Run all tests
poetry run python integration_tests/test_agriculture.py

# Run first 3 tests
poetry run python integration_tests/test_agriculture.py 3

# Run with detailed output (shows full React loop)
poetry run python integration_tests/test_agriculture.py -d

# Run 2 tests with detailed output
poetry run python integration_tests/test_agriculture.py -d 2
```

**What it tests:**
- Weather forecast scenarios
- Historical weather queries
- Agricultural conditions
- Multi-tool workflows
- Edge cases and error handling

**Detailed mode shows:**
- Complete React loop iterations (Thought → Action → Observation)
- Tool selection reasoning
- Execution timing
- Full trajectory analysis

#### 4. Multi-Turn Conversation Tests (`test_multi_turn.py`)

Tests multi-turn conversation capabilities (Note: Currently disabled in test runner).

```bash
poetry run python integration_tests/test_multi_turn.py

# Run with detailed output
poetry run python integration_tests/test_multi_turn.py -d
```

**What it tests:**
- Message ordering and persistence
- Context retention across turns
- Tool usage in conversations
- Conversation history tracking
- Message ID validation

## Environment Configuration

The tests use environment variables from `.env`:

```bash
# MCP Server Configuration
# Docker hostname is automatically replaced with localhost for local testing
MCP_SERVER_URL=http://mcp-server:7778/mcp

# API Configuration (for E2E tests)
API_URL=http://localhost:8000
API_PORT=8000

# Other settings
MOCK_WEATHER=true  # Set to false for real API calls
```

## Test Output Examples

### Successful MCP Connection Test
```
=== Testing MCP Weather Server ===
URL: http://localhost:7778/mcp

1. Connecting to server...
✓ Connected

2. Listing tools...
✓ Found 3 tools:
  - get_weather_forecast
  - get_historical_weather
  - get_agricultural_conditions
✓ All expected tools found!

3. Testing each tool:
  ✓ Forecast: Weather forecast for Seattle (3 days)
  ✓ Historical: Historical weather for Seattle from 2024-01-01 to 2024-01-07
  ✓ Agricultural: Agricultural conditions for Iowa (5 days)

✓ All tests passed!
```

### Test Runner Summary
```
============================================================
SUMMARY
============================================================
Tests run:     2
Passed:        2
Failed:        0

Overall:       PASSED
```

## Troubleshooting

### Common Issues

1. **MCP Connection Failed**
   ```
   Client failed to connect: [Errno 8] nodename nor servname provided, or not known
   ```
   - The test automatically handles Docker hostname resolution
   - Ensure MCP server container is running: `docker ps | grep mcp`
   - Check port 7778 is mapped: `docker ps` should show `0.0.0.0:7778->7778/tcp`

2. **API Connection Refused**
   - Ensure all services are running: `docker-compose ps`
   - Check API health: `curl http://localhost:8000/health`
   - Verify Temporal is accessible: http://localhost:8080

3. **Workflow Timeouts**
   - Check worker logs: `docker-compose logs worker`
   - Ensure worker is processing tasks
   - Verify MCP server is responding

### Debugging Tips

- Add `-d` flag to tests for detailed output
- Check Docker logs: `docker-compose logs -f [service]`
- Verify environment variables are loaded (tests print this)
- Use curl to test endpoints directly

## API Changes Note

The tests have been updated to work with the new conversation API structure:
- Uses `message_count` and `latest_message` instead of `conversation_history`
- Fetches conversation updates via `/conversation` endpoint
- Handles UUID-based message IDs
- Includes conversion helpers for backward compatibility in tests

## Adding New Tests

Follow the simple pattern:

```python
#!/usr/bin/env python3
"""Test description here."""
import asyncio
import sys

async def test_something():
    """Test specific functionality."""
    print("Testing something...")
    # Test logic here
    print("✓ Test passed!")
    return True

async def main():
    success = await test_something()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

Keep tests:
- Simple and focused
- Self-contained
- With clear console output
- Using standard exit codes (0 = success, 1 = failure)