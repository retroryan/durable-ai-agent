# MCP Tools Example Queries

This document provides example queries that demonstrate the usage of MCP-enabled tools in the Durable AI Agent system.

## Overview

The system now includes both traditional and MCP-enabled versions of weather tools. The MCP tools are automatically routed through the `MCPExecutionActivity` and call remote MCP servers instead of local Python code.

## Example Queries

### 1. Weather Forecast via MCP

```
weather: What's the weather forecast for Seattle using the MCP forecast service?
```

Expected behavior:
- React agent selects `get_weather_forecast_mcp` tool
- Workflow routes to `MCPExecutionActivity` (300s timeout)
- MCP client calls the weather proxy server
- Returns forecast data from MCP service

### 2. Historical Weather via MCP

```
weather: Get historical weather data for Chicago from last week using the MCP historical service
```

Expected behavior:
- React agent selects `get_historical_weather_mcp` tool
- Routes through MCP execution path
- Retrieves historical data from MCP server
- Returns past weather conditions

### 3. Agricultural Conditions via MCP

```
weather: Check agricultural conditions for corn farming in Iowa using the MCP agricultural service
```

Expected behavior:
- React agent selects `get_agricultural_conditions_mcp` tool
- Executes via MCP with crop-specific parameters
- Returns soil moisture, GDD, and other metrics

### 4. Comparing Traditional vs MCP Tools

```
weather: Compare the weather forecast from both traditional and MCP services for Denver
```

Expected behavior:
- React agent may call both tools in sequence
- `get_weather_forecast` executes locally
- `get_weather_forecast_mcp` executes via MCP
- Both results included in trajectory

### 5. Complex Multi-Tool Query

```
weather: I'm planning to plant soybeans in Des Moines. Check current conditions, 7-day forecast, and historical patterns from last year using MCP services.
```

Expected behavior:
- Multiple MCP tool calls in sequence
- Each tool execution tracked in trajectory
- Comprehensive agricultural analysis

## Mock Mode Testing

When `TOOLS_MOCK=true` is set in the environment:

```bash
# In worker.env or .env
TOOLS_MOCK=true
```

All MCP tools will return predictable mock data:
- Consistent temperature values
- Fixed precipitation patterns
- Standardized agricultural metrics
- `"mock": true` flag in responses

## Debugging MCP Tool Execution

### Check Tool Selection

The React agent's thought process shows tool selection:
```
thought_0: "The user wants weather forecast via MCP, I should use get_weather_forecast_mcp"
tool_name_0: "get_weather_forecast_mcp"
```

### Verify MCP Routing

Worker logs show activity routing:
```
INFO: Executing MCP tool: get_weather_forecast_mcp
INFO: MCP client connecting to http://weather-proxy:8000/mcp
```

### Inspect Trajectory

The complete trajectory includes:
- `thought_{idx}`: Agent reasoning
- `tool_name_{idx}`: Selected tool (ends with _mcp)
- `tool_args_{idx}`: Tool arguments
- `observation_{idx}`: MCP server response

## Common Patterns

### 1. Explicit MCP Tool Request

Users can explicitly request MCP tools:
```
weather: Use the MCP forecast service to check weather in Portland
```

### 2. Tool Set Selection

The agriculture tool set includes both types:
- 3 traditional tools
- 3 MCP-enabled tools
- Total of 6 tools available

### 3. Error Handling

MCP tool errors are gracefully handled:
- Connection errors → retry with backoff
- Server errors → logged in trajectory
- Timeout errors → 300s timeout for MCP vs 30s for traditional

## Testing in Docker

```bash
# Start with mock mode
TOOLS_MOCK=true docker-compose --profile weather_proxy up -d

# Test via API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "weather: Check forecast in New York using MCP service",
    "user_id": "test-user"
  }'

# Check trajectory in response
# Look for tool_name_0: "get_weather_forecast_mcp"
```

## Benefits of MCP Tools

1. **Distributed Execution**: Tools run on separate servers
2. **Language Agnostic**: MCP servers can be in any language
3. **Better Scalability**: Independent scaling of tool servers
4. **Fault Isolation**: Tool failures don't crash workers
5. **Mock Mode**: Predictable testing without external APIs

## Future Enhancements

- Dynamic tool discovery from MCP servers
- Automatic MCP tool registration
- Tool versioning and compatibility
- Performance metrics per tool type
- Fallback from MCP to traditional tools