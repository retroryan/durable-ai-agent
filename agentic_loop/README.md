# Agentic Loop Demo

## What is the Agentic Loop?

The Agentic Loop implements a React (Reason-Act) pattern for intelligent tool selection and execution. It uses DSPy to create a multi-step reasoning system where an AI agent:

1. **Thinks** about what needs to be done
2. **Selects** the appropriate tool and arguments
3. **Observes** the results
4. **Iterates** until the task is complete

This creates a transparent reasoning trajectory that shows exactly how the AI arrived at its answer.

## Quick Start

### Prerequisites
- Python with Poetry installed
- Dependencies installed via `poetry install`

### Running the Demo

```bash
# Run all test cases for agriculture tools (uses TOOLS_MOCK env var, defaults to true)
poetry run python agentic_loop/demo_react_agent.py agriculture

# Run a specific test case (e.g., test case 2)
poetry run python agentic_loop/demo_react_agent.py agriculture 2

# Run with weather tools
poetry run python agentic_loop/demo_react_agent.py weather

# Run with real API calls instead of mock results
TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture

# Run specific test with real API calls
TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture 2
```

**Note**: By default, the demo uses mock results for predictable testing (controlled by `TOOLS_MOCK=true` in the environment). Set `TOOLS_MOCK=false` to make actual API calls to weather services.

### Environment Configuration

The demo uses environment variables to control how weather/agriculture tools operate. These settings only affect the three MCP-based weather tools - other tools in the system are not affected.

#### Two Independent Settings

1. **`MCP_USE_STDIO`** - Controls HOW tools connect to MCP servers
   - `true`: Use stdio (direct process communication, no Docker needed)
   - `false`: Use HTTP (requires MCP servers running via Docker OR locally)

2. **`TOOLS_MOCK`** - Controls WHAT DATA tools return
   - `true`: Return mock/simulated weather data for predictable testing
   - `false`: Make actual API calls to OpenMeteo weather services

These settings are independent - you can use any combination:
- Stdio + Mock data (fast local testing)
- Stdio + Real data (real weather without Docker)
- HTTP + Mock data (test Docker setup with predictable data)
- HTTP + Real data (full production-like setup)

#### Quick Start Examples

```bash
# Run with environment defaults (or .env file if present)
poetry run python agentic_loop/demo_react_agent.py agriculture

# Real weather data via stdio (no Docker needed)
TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture

# Use HTTP transport with local servers (no Docker)
poetry run python scripts/run_mcp_servers.py &  # Start servers in background
MCP_USE_STDIO=false poetry run python agentic_loop/demo_react_agent.py agriculture
poetry run python scripts/stop_mcp_servers.py  # Stop servers when done

# Use HTTP transport with Docker proxy
docker-compose --profile weather_proxy up -d
MCP_USE_PROXY=true MCP_URL=http://localhost:8001/mcp MCP_USE_STDIO=false poetry run python agentic_loop/demo_react_agent.py agriculture

# Full production-like setup (HTTP + real data with Docker)
docker-compose --profile weather_proxy up -d
MCP_USE_PROXY=true MCP_URL=http://localhost:8001/mcp MCP_USE_STDIO=false TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture
```

#### HTTP Server Options

When using HTTP transport (`MCP_USE_STDIO=false`), you have two options:

1. **Local Servers** (no Docker required):
   ```bash
   # Start servers
   poetry run python scripts/run_mcp_servers.py
   
   # In another terminal, run the demo
   MCP_USE_STDIO=false poetry run python agentic_loop/demo_react_agent.py agriculture
   
   # Stop servers when done
   poetry run python scripts/stop_mcp_servers.py
   ```

2. **Docker with Proxy**:
   ```bash
   # Start Docker services
   docker-compose --profile weather_proxy up -d
   
   # Run demo (configure .env or use environment vars)
   MCP_USE_PROXY=true MCP_URL=http://localhost:8001/mcp MCP_USE_STDIO=false poetry run python agentic_loop/demo_react_agent.py agriculture
   ```

#### Using .env File

```bash
# Copy example configuration
cp agentic_loop/.env.example agentic_loop/.env

# Edit .env to set your preferred configuration
# Then just run normally:
poetry run python agentic_loop/demo_react_agent.py agriculture
```

### Available Tool Sets

- **agriculture** - Includes weather forecast, historical weather, and agricultural conditions tools
- **weather** - Basic weather tools for forecast and historical data

### What to Expect

The demo will:
1. Set up the LLM connection
2. Run test queries through the React agent
3. Show the reasoning process (thoughts, tool selections, observations)
4. Extract a final answer from the reasoning trajectory
5. Display performance metrics

### Example Output

```
🔄 React Agent Execution
[ReactAgent] Starting forward pass - Iteration: 1
[ReactAgent] LLM response - Thought: 'I need to get weather for NYC...', Tool: 'get_weather_forecast'
✓ React loop completed in 11.11s
  Iterations: 3
  Tools used: get_weather_forecast

📝 Extract Agent
Final answer: The weather forecast for New York City shows...
```