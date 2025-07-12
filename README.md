# Durable AI Agent

A simplified demonstration of durable AI conversations using Temporal workflows. This project shows how to build reliable, persistent workflows without complex AI logic.

## Overview

This project is a minimal implementation that:
- Demonstrates Temporal workflow patterns
- Shows activity execution with retry logic
- Maintains state across workflow restarts
- Provides a clean foundation for extension

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.10+ (for local development)
- Node.js 20+ (for frontend development)
- Poetry (for Python dependency management)

### Setting up Poetry

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install project dependencies**:
   ```bash
   poetry install
   ```

3. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

## Architecture

The system consists of:
- **Workflow**: Simple workflow that tracks query count and executes activities
- **Activity**: Calls a hardcoded tool (find_events) with fixed parameters
- **API**: FastAPI server for workflow management
- **Frontend**: React UI for chat interaction


### Running the Complete System

1. **Set up environment**
   ```bash
   cp .env.example .env
   ```

2. **Start all services with Docker Compose**
   ```bash
   docker-compose up
   ```

3. **Access the applications**
   - 🌐 **Frontend (Chat UI)**: http://localhost:3000
   - 📡 **API Server**: http://localhost:8000
   - 📚 **API Documentation**: http://localhost:8000/docs
   - ⚙️ **Temporal UI**: http://localhost:8080

### What Gets Started

Docker Compose will start the following services:
- **PostgreSQL**: Database for Temporal
- **Temporal Server**: Workflow orchestration engine
- **Temporal UI**: Web interface for monitoring workflows
- **API Server**: FastAPI backend at port 8000
- **Worker**: Processes Temporal workflows and activities
- **Frontend**: React chat interface at port 3000

### Using the Chat Interface

1. Open http://localhost:3000 in your browser
2. Type a message in the input field
3. The system will:
   - Create a new Temporal workflow
   - Execute the find_events activity
   - Return information about events in Melbourne
4. The workflow ID and status are displayed in the header
5. Click "New Conversation" to start a fresh workflow

### Development Mode

For local development without Docker:

```bash
# Terminal 1: Start Temporal (requires Temporal CLI)
temporal server start-dev

# Terminal 2: Start the worker
poetry install
poetry run python worker/main.py

# Terminal 3: Start the API server
poetry run python api/main.py

# Terminal 4: Start the frontend
cd frontend
npm install
npm run dev
```

## Running Tests

The project includes comprehensive test suites covering unit tests, API integration tests, and MCP integration tests.

### Prerequisites
1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Create .env file: `cp .env.example .env`

### Unit Tests
```bash
# Run unit tests
poetry run pytest tests/

# Run with verbose output
poetry run pytest tests/ -v
```

### Integration Tests

The project has two types of integration tests:

#### 1. API Integration Tests (pytest-based)
These test the API endpoints and workflow functionality through HTTP requests.

#### 2. MCP Integration Tests (direct Python programs)
These test MCP client functionality and are **intentionally direct Python programs (not pytest)** to avoid complexity and issues with async test runners and connection pooling.

### Running All Integration Tests

**Quick Start - Run Everything**:
```bash
# 1. Start all services
docker-compose up -d

# 2. Run all integration tests (API + MCP)
python integration_tests/run_integration_tests.py

# 3. Clean up
docker-compose down
```

**Integration Test Runner Options**:
```bash
# Run all tests (API + MCP)
python integration_tests/run_integration_tests.py

# Skip HTTP-based MCP tests (stdio only)
python integration_tests/run_integration_tests.py --no-http

# Skip API tests (MCP only)
python integration_tests/run_integration_tests.py --no-api

# Run only MCP tests
python integration_tests/run_integration_tests.py --mcp-only
```

### Running Individual Test Suites

#### API Integration Tests (pytest-based)
**Prerequisites**: Full stack must be running (`docker-compose up`)

```bash
# Run all API integration tests
poetry run pytest integration_tests/ -v

# Run specific test files
poetry run pytest integration_tests/test_api_endpoints.py -v
poetry run pytest integration_tests/test_workflow_integration.py -v

# Run by test category
poetry run pytest integration_tests/ -m api -v
poetry run pytest integration_tests/ -m workflow -v

# Run with custom API URL
API_URL=http://localhost:8001 poetry run pytest integration_tests/ -v
```

**API Test Coverage**:
- ✅ Health and root endpoints
- ✅ Chat endpoint workflow creation
- ✅ Workflow status and query endpoints
- ✅ Error handling (404, 422 responses)
- ✅ Workflow lifecycle management
- ✅ Query count persistence
- ✅ Multiple workflow isolation
- ✅ Concurrent workflow execution

#### MCP Integration Tests (direct Python programs)

**Why direct Python programs?**
- Pytest's async handling conflicts with MCP client event loops
- Connection pooling issues when running multiple tests
- Simpler debugging and clearer error messages
- Direct control over test execution and cleanup

**Running Individual MCP Tests**:
```bash
# Run individual tests directly (each loads .env independently)
python integration_tests/test_stdio_client.py
python integration_tests/test_http_client.py  # Requires HTTP server running
```

**MCP Test Coverage**:
- ✅ Stdio client connection and tool invocation
- ✅ HTTP client connection and tool invocation
- ✅ Connection reuse and cleanup
- ✅ Multiple tool invocations
- ✅ Environment configuration loading

### Environment Configuration

All tests load configuration from the `.env` file. Each test (both pytest and direct Python) loads the `.env` file independently, so they can be run separately:

```bash
# API Configuration
API_URL=http://localhost:8000

# MCP Server Configuration
MCP_FORECAST_SERVER_HOST=localhost
MCP_FORECAST_SERVER_PORT=7778
MCP_FORECAST_SERVER_URL=http://localhost:7778/mcp
```

### Running All Tests

**Complete Test Suite**:
```bash
# 1. Start services
docker-compose up -d

# 2. Run unit tests
poetry run pytest tests/ -v

# 3. Run all integration tests (API + MCP)
python integration_tests/run_integration_tests.py

# 4. Clean up
docker-compose down
```

**Alternative - Run Test Types Separately**:
```bash
# 1. Start services
docker-compose up -d

# 2. Run unit tests
poetry run pytest tests/ -v

# 3. Run API integration tests
poetry run pytest integration_tests/ -v

# 4. Run MCP integration tests
python integration_tests/run_integration_tests.py --mcp-only

# 5. Clean up
docker-compose down
```

### Test Results Summary

**Unit Tests** (`tests/`):
- ✅ Basic workflow execution
- ✅ Query count functionality  
- ✅ Workflow ID handling
- ✅ Activity execution

**API Integration Tests** (`integration_tests/` - pytest):
- ✅ 8 API endpoint tests
- ✅ 7 workflow integration tests
- ✅ Error handling and validation
- ✅ Concurrent execution testing

**MCP Integration Tests** (`integration_tests/` - direct Python):
- ✅ Stdio client testing
- ✅ HTTP client testing
- ✅ Environment-driven configuration
- ✅ Connection management

### Troubleshooting Tests

**API Tests Skipped**:
- Ensure services are running: `docker-compose up`
- Check API health: `curl http://localhost:8000/health`
- Verify Temporal UI: http://localhost:8080

**MCP Tests Failing**:
- For HTTP tests: Ensure MCP server is running on port 7778
- Check `.env` file configuration
- Run tests individually for better error messages

All tests are passing! The project successfully demonstrates:
- Temporal workflow patterns with proper state management
- Activity execution with retry policies
- Query handlers for workflow introspection
- Integration with external tools and MCP servers
- Full API integration testing

## API Endpoints

- `POST /chat` - Start a workflow with a message
- `GET /workflow/{workflow_id}/status` - Get workflow status
- `GET /workflow/{workflow_id}/query` - Query workflow state
- `GET /health` - Health check
- `GET /docs` - API documentation

## Activities

The project includes several Temporal activities that demonstrate MCP (Model Context Protocol) integration patterns:

### Available Activities

1. **weather_forecast_activity.py** 
   - Calls forecast MCP server for weather predictions
   - Returns formatted weather data for New York (3 days)
   - Located at: `activities/weather_forecast_activity.py:12`

2. **weather_historical_activity.py**
   - Calls historical MCP server for past weather data
   - Returns historical weather for Brisbane (yesterday's date)
   - Located at: `activities/weather_historical_activity.py:11`

3. **agricultural_activity.py**
   - Calls agricultural MCP server for farming conditions  
   - Returns soil moisture, evapotranspiration, and growing conditions
   - Located at: `activities/agricultural_activity.py:10`

4. **find_events_activity.py**
   - Legacy activity with hardcoded tool execution
   - Returns event information for Melbourne
   - Located at: `activities/find_events_activity.py:12`

### MCP Utilities

The `activities/mcp_utils.py` module provides common utilities for all MCP activities:

- **`get_user_display_name()`** - Extract display names for personalization
- **`get_mcp_server_config()`** - Environment-based MCP server configuration
- **`call_mcp_tool()`** - Generic MCP tool calling with error handling and logging
- **`parse_mcp_result()`** - Parse MCP responses consistently across activities
- **`create_error_response()`** - Generate standardized error responses

### Activity Pattern

All MCP activities follow a consistent pattern:
```python
@activity.defn
async def activity_name(user_message: str, user_name: str = "anonymous") -> Dict[str, Any]:
    try:
        result = await call_mcp_tool(
            service_name="service",
            tool_name="tool_name", 
            tool_args={"arg": "value"},
            user_name=user_name
        )
        return {"message": "friendly response", "data": result}
    except Exception as e:
        return create_error_response(user_name, str(e))
```

## Project Structure

```
durable-ai-agent/
├── workflows/          # Temporal workflows
├── activities/         # Temporal activities with MCP integrations
│   ├── mcp_utils.py           # Common MCP utilities
│   ├── weather_forecast_activity.py    # Weather forecast activity
│   ├── weather_historical_activity.py  # Historical weather activity
│   ├── agricultural_activity.py        # Agricultural conditions activity
│   └── find_events_activity.py         # Legacy event finding activity
├── tools/             # Tool implementations
├── models/            # Data models
├── shared/            # Shared utilities
├── worker/            # Worker process
├── api/               # API server
├── mcp_proxy/         # Unified MCP proxy server
│   ├── simple_proxy.py       # Main proxy implementation
│   ├── run_docker.sh         # Docker compose startup script
│   ├── test_docker.sh        # Docker testing script
│   └── stop_docker.sh        # Docker cleanup script
├── frontend/          # React UI
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   └── services/     # API client
│   └── Dockerfile        # Frontend container
├── integration_tests/ # Integration test suites
│   └── test_proxy_integration.py  # Proxy integration tests
├── docker-compose.yml  # Service orchestration with profiles
└── tests/             # Test suites
```

## Key Simplifications

- No AI/LLM integration (focuses on Temporal workflow patterns)
- Multiple MCP activities with standardized patterns
- Fixed parameters for demo purposes (various cities and conditions)
- Minimal state management (query count tracking)
- No complex routing or planning (simple activity execution)
- Unified MCP proxy for simplified service access

## Temporal Best Practices

### Key Points from Temporal Documentation

- **Activity IDs** are only unique within a workflow run, not globally
- **Task Tokens** provide unique identification for activity executions
- **Workflow IDs** are unique within a namespace and commonly include business identifiers
- **User Context**: Always pass user-specific data explicitly as parameters rather than relying on implicit context
- **Activity Context**: Activities have access to workflow ID, activity ID, task queue, and attempt number through `activity.info()`

## Next Steps

See `durable-ai-agent.md` for the complete implementation plan and architecture guide.

## Integration Tests Details

The project includes comprehensive integration tests with a two-tier approach:

1. **API Integration Tests** (pytest-based) - Test API endpoints with HTTP requests
2. **MCP Integration Tests** (direct Python programs) - Test MCP client functionality

### Integration Test Structure

```
integration_tests/
├── README.md              # Integration test documentation
├── conftest.py            # Pytest configuration and fixtures
├── utils/                 # Test utilities
│   ├── api_client.py      # HTTP client wrapper for API calls
│   └── test_helpers.py    # Assertion helpers and utilities
├── test_api_endpoints.py  # Tests for API endpoints (pytest)
├── test_workflow_integration.py  # Tests for workflow functionality (pytest)
├── test_stdio_client.py  # MCP stdio client test (direct Python)
├── test_http_client.py   # MCP HTTP client test (direct Python)
└── run_integration_tests.py  # MCP test runner (direct Python)
```

### API Test Utilities (pytest-based)

**DurableAgentAPIClient** (`utils/api_client.py`):
- Async HTTP client using `httpx`
- Methods for all API endpoints: `chat()`, `get_workflow_status()`, `query_workflow()`
- Helper methods like `wait_for_workflow_completion()`
- Configurable timeout and base URL

**WorkflowAssertions** (`utils/test_helpers.py`):
- `assert_workflow_started()` - Verifies workflow creation
- `assert_workflow_completed()` - Checks completion status
- `assert_events_found()` - Validates event finder results
- `get_workflow_id()`, `get_event_count()`, `get_query_count()` - Extract data from responses

### Test Coverage

**API Endpoint Tests** (pytest):
- ✅ Health check endpoint (`/health`)
- ✅ Root endpoint (`/`)
- ✅ Chat endpoint (`/chat`) - workflow creation
- ✅ Workflow status (`/workflow/{id}/status`)
- ✅ Workflow query (`/workflow/{id}/query`)
- ✅ Error handling (404, 422 responses)

**Workflow Integration Tests** (pytest):
- ✅ Activity execution verification
- ✅ Query count state persistence
- ✅ Multiple workflow isolation
- ✅ Custom workflow ID support
- ✅ Concurrent workflow execution
- ✅ Response format validation

**MCP Integration Tests** (direct Python):
- ✅ Stdio client connection and tool invocation
- ✅ HTTP client connection and tool invocation
- ✅ Connection reuse and cleanup
- ✅ Multiple tool invocations
- ✅ Environment configuration loading

### Running Integration Tests

**API Tests** (pytest-based):
```bash
# Prerequisites: Start all services
docker-compose up

# Run all API integration tests
poetry run pytest integration_tests/ -v

# Run only API tests
poetry run pytest integration_tests/test_api_endpoints.py -v

# Run only workflow tests
poetry run pytest integration_tests/test_workflow_integration.py -v

# Run by marker
poetry run pytest integration_tests/ -m api -v
poetry run pytest integration_tests/ -m workflow -v

# Run with custom API URL
API_URL=http://localhost:8001 poetry run pytest integration_tests/ -v
```

**MCP Tests** (direct Python programs):
```bash
# Run all MCP integration tests
python integration_tests/run_integration_tests.py

# Run without HTTP tests (stdio only)
python integration_tests/run_integration_tests.py --no-http

# Run individual tests
python integration_tests/test_stdio_client.py
python integration_tests/test_http_client.py
```

### Key Features

**API Tests**:
- **Async Testing**: All tests use `pytest-asyncio` for async/await support
- **Fixtures**: Session-scoped API client, fresh workflow IDs, test configuration
- **Markers**: Tests are marked with `@pytest.mark.api` or `@pytest.mark.workflow`
- **Real HTTP Calls**: Tests make actual HTTP requests to the running API server
- **Comprehensive Assertions**: Helper functions for common workflow validations
- **Error Handling**: Tests verify both success and error scenarios

**MCP Tests**:
- **Direct Python Programs**: Avoid pytest complexity with async event loops
- **Environment Configuration**: Each test loads `.env` file independently
- **Connection Management**: Proper cleanup and reuse testing
- **Simpler Debugging**: Direct execution with clear error messages

### Writing New Integration Tests

**API Test Example** (pytest):
```python
@pytest.mark.api
@pytest.mark.asyncio
async def test_my_feature(api_client):
    response = await api_client.chat("Test message")
    WorkflowAssertions.assert_workflow_completed(response)
```

**MCP Test Example** (direct Python):
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

The integration tests ensure the entire system works correctly end-to-end, complementing the unit tests that test individual components in isolation.

## Proxy Testing

The MCP proxy server provides a unified endpoint for multiple weather services. Here's how to run and test it.

### Running the Proxy

**Start the proxy server**:
```bash
# From the project root directory
python -m mcp_proxy.simple_proxy

# The proxy will start on http://localhost:8000/mcp
# (Use port 8001 if 8000 is in use)
```

### Testing the Proxy

**Quick test script**:
```bash
# Run the simple test script
python mcp_proxy/test_simple_proxy.py
```

This will:
- Connect to the proxy at http://localhost:8000/mcp
- List all available tools (8 tools from 3 services)
- Test calling tools from each service
- Display the results

**Expected output**:
```
Connecting to proxy at http://localhost:8000/mcp...
✅ Connected to proxy!

Found 8 tools:
  - forecast_get_forecast: Get weather forecast
  - forecast_get_hourly_forecast: Get hourly weather forecast
  - current_get_current_weather: Get current weather
  - current_get_temperature: Get current temperature
  - current_get_conditions: Get current conditions
  - historical_get_historical_weather: Get historical weather
  - historical_get_climate_average: Get climate average
  - historical_get_weather_records: Get weather records

Testing tool calls...
Current weather result: {...}
Forecast result: {...}
Historical result: {...}
```

### Docker Compose Profiles

The project uses Docker Compose profiles to manage different service configurations:

**Weather Proxy (Default)**:
```bash
# Start the unified weather proxy (includes forecast, current, historical services)
docker-compose --profile weather_proxy up -d weather-proxy

# Or use the convenience script
./mcp_proxy/run_docker.sh

# Access proxy at: http://localhost:8001/mcp
```

**Individual Forecast Service**:
```bash
# Start only the forecast MCP server
docker-compose --profile forecast up -d forecast-mcp

# Access forecast service at: http://localhost:7778/mcp
```

### Docker Testing

**Simple scripts for Docker operations**:
```bash
# Navigate to the proxy directory
cd mcp_proxy/

# Build and run the unified weather proxy with docker-compose
./run_docker.sh

# Test the running proxy
./test_docker.sh

# Stop and remove containers
./stop_docker.sh
```

The scripts handle:
- `run_docker.sh` - Starts the weather proxy using docker-compose profile
- `test_docker.sh` - Tests the proxy with MCP client calls
- `stop_docker.sh` - Stops and removes containers with docker-compose

### Integration Testing

**Proxy Integration Test**:
```bash
# Start the weather proxy
./mcp_proxy/run_docker.sh

# Run integration tests against the proxy
python integration_tests/test_proxy_integration.py
```

This test verifies:
- ✅ Proxy connection and unified tool listing (8 tools from 3 services)
- ✅ Current weather, forecast, and historical tool calls
- ✅ Connection reuse and multiple sequential operations
- ✅ All services accessible through single endpoint

### Manual Testing with curl

**List all tools**:
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

**Call a specific tool**:
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "forecast_get_forecast",
      "arguments": {"location": "Sydney", "days": 3}
    },
    "id": 2
  }'
```

### Using with MCP Client

```python
from fastmcp.client import Client

async with Client("http://localhost:8001/mcp") as client:
    # List tools
    tools = await client.list_tools()
    
    # Call a tool
    result = await client.call_tool(
        "current_get_current_weather",
        {"location": "Melbourne"}
    )
```

### Proxy Architecture

The proxy uses FastMCP's built-in features:
- `FastMCP.mount()` to combine multiple services
- `proxy.run(transport="streamable-http")` for HTTP transport
- Automatic session management and protocol handling

This simple approach reduces complexity from hundreds of lines to about 20 lines of code while providing full MCP protocol support.