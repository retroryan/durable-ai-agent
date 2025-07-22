# Agentic Loop Demo

## Quick Start

```bash
# 1. Configure your LLM provider in the parent .env file
#    (see .env.example for examples - e.g., ANTHROPIC_API_KEY, OPENAI_API_KEY, or Ollama settings)

# 2. Start MCP servers locally (in a separate terminal)
poetry run python scripts/run_mcp_servers.py

# 3. Run the demo
MCP_USE_PROXY=false poetry run python agentic_loop/demo_react_agent.py agriculture
```

That's it! The demo will run with mock weather data. To use real weather data, add `TOOLS_MOCK=false`:

```bash
MCP_USE_PROXY=false TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture
```

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

**Important**: The demo requires:
1. LLM configuration in your .env file (API keys, provider settings) - see the "DEMO CONFIGURATION SECTION" in .env.example
2. MCP servers running locally

#### Quick Start

```bash
# 1. Ensure your .env file has LLM configuration (see .env.example for examples)

# 2. Start MCP servers locally (in a separate terminal)
poetry run python scripts/run_mcp_servers.py

# The servers will run on:
# - Forecast server: http://localhost:7778/mcp
# - Historical server: http://localhost:7779/mcp
# - Agricultural server: http://localhost:7780/mcp

# 3. Run the demo with environment overrides for local MCP servers
MCP_USE_PROXY=false poetry run python agentic_loop/demo_react_agent.py agriculture

# Or to use real weather data:
MCP_USE_PROXY=false TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture
```

#### Demo Commands

```bash
# Run all test cases for agriculture tools (with mock data)
MCP_USE_PROXY=false poetry run python agentic_loop/demo_react_agent.py agriculture

# Run a specific test case (e.g., test case 2)
MCP_USE_PROXY=false poetry run python agentic_loop/demo_react_agent.py agriculture 2

# Run with weather tools
MCP_USE_PROXY=false poetry run python agentic_loop/demo_react_agent.py weather

# Run with real API calls instead of mock results
MCP_USE_PROXY=false TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture

# Run specific test with real API calls
MCP_USE_PROXY=false TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture 2
```

**Note**: By default, the demo uses mock results for predictable testing (controlled by `TOOLS_MOCK=true` in the environment). Set `TOOLS_MOCK=false` to make actual API calls to weather services.

### Environment Configuration

The demo uses environment variables to control how weather/agriculture tools operate. These settings only affect the three MCP-based weather tools - other tools in the system are not affected.

#### Key Settings

1. **`TOOLS_MOCK`** - Controls WHAT DATA tools return
   - `true`: Return mock/simulated weather data for predictable testing (default)
   - `false`: Make actual API calls to OpenMeteo weather services

2. **`MCP_USE_PROXY`** - Controls which MCP endpoint to use
   - `true`: Use the unified proxy server (default when using Docker)
   - `false`: Connect to individual MCP servers directly

3. **`MCP_URL`** - The MCP server URL
   - Default: `http://localhost:8001/mcp` (proxy)
   - For individual servers: Use ports 7778, 7779, 7780

#### Quick Start Examples

```bash
# Run with local MCP servers (mock data)
MCP_USE_PROXY=false poetry run python agentic_loop/demo_react_agent.py agriculture

# Real weather data with local MCP servers
MCP_USE_PROXY=false TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture

# Use Docker proxy (mock data)
docker-compose --profile weather_proxy up -d
MCP_USE_PROXY=true MCP_URL=http://localhost:8001/mcp poetry run python agentic_loop/demo_react_agent.py agriculture

# Full production-like setup (real data with Docker)
docker-compose --profile weather_proxy up -d
MCP_USE_PROXY=true MCP_URL=http://localhost:8001/mcp TOOLS_MOCK=false poetry run python agentic_loop/demo_react_agent.py agriculture
```

#### MCP Server Options

You have two options for running MCP servers:

1. **Local Servers** (no Docker required):
   ```bash
   # Start servers
   poetry run python scripts/run_mcp_servers.py
   
   # In another terminal, run the demo
   MCP_USE_PROXY=false poetry run python agentic_loop/demo_react_agent.py agriculture
   
   # Stop servers when done
   poetry run python scripts/stop_mcp_servers.py
   ```

2. **Docker with Proxy**:
   ```bash
   # Start Docker services
   docker-compose --profile weather_proxy up -d
   
   # Run demo
   MCP_USE_PROXY=true MCP_URL=http://localhost:8001/mcp poetry run python agentic_loop/demo_react_agent.py agriculture
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