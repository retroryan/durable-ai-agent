# Durable AI Agent

A demonstration of how to combine Temporal Workflows and Workers with an Agentic AI Loop that includes automatic execution capabilities. This project shows how to build reliable, persistent AI agents that can reason, plan, and execute actions while maintaining state across restarts and failures.

## Overview

This project demonstrates the integration of:

**Temporal Workflows & Workers**: The foundation provides durable execution with automatic retry, state persistence, and fault tolerance. Workflows can be long-running conversations that survive system restarts and continue from where they left off.

**Agentic AI Loop**: When a user message contains the magic word "weather", the system triggers a fully custom agentic workflow modeled after DSPy React patterns. This agent can reason about problems, select appropriate tools, execute actions, and observe results in an iterative loop until the task is complete.

**Multi-Step Reasoning**: The agentic loop breaks down complex requests into smaller steps, uses available tools to gather information, and synthesizes results. It can handle multi-turn reasoning where each step builds on previous observations.

**Tool Integration**: The system includes several MCP (Model Context Protocol) servers for weather forecasting, historical weather data, and agricultural conditions. We also have a built-in MCP client manager that handles connections and tool execution. A next step will be to add these as tools to fully support MCP integration across all workflows.

**Fallback Patterns**: For simpler requests, the system falls back to direct activity execution for weather historical data, agriculture conditions, or basic event finding, ensuring the system works for both simple and complex scenarios.

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


### Running the Complete System (Recommended)

1. **Set up environment files**
   ```bash
   cp .env.example .env
   cp worker.env .worker.env
   ```
   **Note**: Make sure `.worker.env` is copied from `worker.env` and is not in the samples. The existing `.env` file should remain as is.

2. **Start all services with the convenience script**
   ```bash
   ./run_docker.sh
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
3. The system supports several types of messages (currently hard-coded in workflows/simple_agent_workflow.py):
   - **"weather"** - Triggers the full agentic workflow with a custom agentic loop modeled off DSPy React. This agent can reason through complex weather-related queries, select appropriate tools, and execute multi-step analysis.
   - **"historical"** - Calls the weather historical activity for past weather data
   - **"agriculture"** - Calls the agricultural activity for farming conditions
   - **Any other message** - Defaults to the find_events activity (legacy behavior)

**Magic Word**: The word "weather" triggers the full agentic workflow with a fully custom agentic loop modeled off DSPy React. This includes multi-step reasoning, tool selection, action execution, and result synthesis. Currently it is hard-coded to use the tool set from the worker.env configuration. In the future, the first call could be a classification agent which decides which tool set(s) to use.

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

### Integration Tests

The main integration test is a plain Python program:

```bash
poetry run python integration_tests/test_weather_api.py
```

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