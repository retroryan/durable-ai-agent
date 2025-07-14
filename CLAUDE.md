# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## File Exclusions

When searching or analyzing this codebase, please ignore:
- `.venv/` - Virtual environment files
- `.history/` - Shell history files
- `.mypy_cache/` - MyPy cache files
- `__pycache__/` - Python bytecode cache
- `node_modules/` - Node.js dependencies

## Project Overview

This is a Python-based distributed workflow application demonstrating durable AI conversation patterns using Temporal, with a **Custom Built Agentic AI Loop using DSPy and Multi-Step Reasoning**. The project implements a React (Reason-Act) pattern for intelligent tool selection and execution, using FastAPI for the API server, Temporal for workflow orchestration, and Docker Compose for containerized deployment.

**IMPORTANT: This is a DEMO project designed for simplicity and clarity.** The goal is to maintain a clean, modular, and easy-to-understand codebase that demonstrates core concepts. This is NOT a complex production implementation. When making changes:
- Prioritize simplicity and readability over complex optimizations
- Keep components modular and loosely coupled
- Avoid over-engineering or adding unnecessary complexity
- Focus on demonstrating the core Temporal workflow patterns clearly

## CRITICAL GUIDELINES

**IMPORTANT: Claude must always follow these goals and principles when working on this codebase.**


1. **No Unnecessary Complexity**: Avoid async patterns, complex abstractions, or heavy frameworks

## Key Principles

- **Easy to Understand**: The entire implementation can be grasped in minutes
- **No Workarounds or Hacks**: Never implement compatibility layers, workarounds, or hacks. Always ask the user to handle edge cases, version conflicts, or compatibility issues directly

**IMPORTANT: If there is a question about something or a request requires a complex hack, always ask the user before implementing. Maintain simplicity over clever solutions.**

**IMPORTANT: Never implement workarounds, compatibility layers, or hacks to handle edge cases or version conflicts. Instead, always inform the user of the issue and ask them how they would like to proceed. This keeps the codebase clean and maintainable.**

## Critical Anti-Patterns to Avoid

**ABSOLUTE WARNING: The following anti-patterns are strictly forbidden in this codebase:**

### 1. **Never Mix Async and Sync Code**
- **FORBIDDEN**: Creating async/sync bridges, wrappers, or adapters
- **FORBIDDEN**: Using `asyncio.run()`, `loop.run_until_complete()`, or any sync-to-async conversion
- **FORBIDDEN**: Implementing "compatibility" functions that convert between async and sync
- **WHY**: DSPy is designed for synchronous-only operation. Mixing paradigms creates complexity and defeats the purpose of this simple demo
- **INSTEAD**: If you encounter async code, inform the user and ask how they'd like to proceed

### 2. **Never Create Legacy Migration or Compatibility Layers**
- **FORBIDDEN**: Writing code to handle multiple versions of dependencies
- **FORBIDDEN**: Creating abstractions to support "old" and "new" APIs simultaneously
- **FORBIDDEN**: Implementing fallback mechanisms for deprecated features
- **WHY**: This is a demo project meant to showcase current best practices, not maintain backward compatibility
- **INSTEAD**: Always use the latest stable APIs and inform the user if updates are needed

### 3. **Never Implement Hacks or Workarounds**
- **FORBIDDEN**: Monkey-patching libraries or modules
- **FORBIDDEN**: Using private/internal APIs (anything starting with `_`)
- **FORBIDDEN**: Creating "clever" solutions to bypass limitations
- **WHY**: Hacks make code fragile and hard to understand
- **INSTEAD**: If something doesn't work cleanly, ask the user for guidance

### 4. **Always Ask Before Implementing Complex Solutions**
If any task seems to require:
- Async/sync conversion or bridging
- Compatibility layers or version handling
- Workarounds for library limitations
- Complex abstractions or indirection
- Legacy code support

**STOP IMMEDIATELY** and ask the user how they would like to proceed. Do not assume or implement these patterns proactively.


## Essential Commands

**IMPORTANT: Always use Poetry for running Python commands.** Never use `python` directly - use `poetry run python` instead. This ensures all dependencies are available in the correct virtual environment.

### Development Setup
```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
```

### Running the Application
```bash
# Start all services (recommended)
docker-compose up

# Start with weather proxy (unified MCP services)
docker-compose --profile weather_proxy up

# Start with individual forecast service
docker-compose --profile forecast up

# Access services at:
# - API: http://localhost:8000 (docs at /docs)
# - Temporal UI: http://localhost:8080
# - Weather Proxy: http://localhost:8001/mcp
# - Forecast Service: http://localhost:7778/mcp
```

## Architecture Overview

The application follows a microservices architecture with these key components:

1. **API Server** (`api/`) - FastAPI application providing REST endpoints for workflow management
2. **Worker** (`worker/`) - Processes Temporal workflows and activities
3. **Workflows** (`workflows/`) - Durable workflow definitions
   - `SimpleAgentWorkflow` - Main workflow that routes messages
   - `AgenticAIWorkflow` - Implements React reasoning loop for complex queries
4. **Activities** (`activities/`) - Atomic units of work
   - `ReactAgentActivity` - Performs reasoning and tool selection
   - `ToolExecutionActivity` - Executes selected tools
   - `ExtractAgentActivity` - Synthesizes final answers from reasoning trajectory
5. **Agentic Loop** (`agentic_loop/`) - DSPy-based reasoning components
   - `ReactAgent` - Implements thought → action → observation cycles
   - `ExtractAgent` - Extracts coherent answers from trajectories
6. **Tools** (`tools/`) - Modular tool implementations
   - `ToolRegistry` - Dynamic tool management system
   - `precision_agriculture/` - Weather and farming-specific tools
7. **MCP Proxy** (`mcp_proxy/`) - Unified proxy server combining multiple weather services

### Key Design Patterns

- **Workflow Pattern**: Each conversation is a long-running Temporal workflow that maintains state
- **Agentic Reasoning**: React pattern with trajectory-based state management
- **Tool Registry**: Dynamic tool selection based on query context
- **Child Workflows**: Complex queries spawn specialized child workflows
- **Message Processing**: Messages are processed through activities with automatic retry and error handling
- **Query Pattern**: Workflow state can be queried at any time without affecting execution
- **Signal Pattern**: New messages are sent to workflows via signals

### API Endpoints

- `POST /chat` - Start a new workflow with an initial message
- `GET /workflow/{workflow_id}/status` - Check workflow execution status
- `GET /workflow/{workflow_id}/query` - Query current workflow state

## Agentic AI Loop Architecture

The project implements a sophisticated React (Reason-Act) pattern for intelligent tool selection and execution:

### Core Components

1. **AgenticAIWorkflow** (`workflows/agentic_ai_workflow.py`)
   - Orchestrates the reasoning loop
   - Maintains trajectory state across iterations
   - Limits iterations to prevent infinite loops
   - Returns structured responses with reasoning transparency

2. **ReactAgentActivity** (`activities/react_agent_activity.py`)
   - Performs reasoning cycles (thought → action → observation)
   - Uses DSPy's React pattern for tool selection
   - Returns tool name and arguments for execution

3. **ToolExecutionActivity** (`activities/tool_execution_activity.py`)
   - Executes tools selected by the React agent
   - Updates trajectory with observations
   - Handles tool errors gracefully

4. **ExtractAgentActivity** (`activities/extract_agent_activity.py`)
   - Synthesizes final answers from complete trajectories
   - Uses DSPy's extraction patterns
   - Provides coherent responses based on reasoning history

### Trajectory-Based State Management

The system maintains a "trajectory" dictionary that captures the entire reasoning process:
- `thought_{idx}`: The agent's reasoning at each step
- `tool_name_{idx}`: Selected tool for the step
- `tool_args_{idx}`: Arguments passed to the tool
- `observation_{idx}`: Tool execution results

This provides full transparency and debuggability of the AI's reasoning process.

### Tool Registry System

- **Dynamic Tool Management**: Tools are registered and selected based on configuration
- **Tool Sets**: Different domains have different tool sets (e.g., "agriculture")
- **Modular Design**: Easy to add new tools without modifying core logic

### Precision Agriculture Tools

New weather and farming-specific tools in `tools/precision_agriculture/`:
- **WeatherForecastTool**: Get weather predictions for locations
- **HistoricalWeatherTool**: Access past weather data
- **AgriculturalWeatherTool**: Get farming-specific weather conditions

## Activities and MCP Integration

The project includes several Temporal activities:

### Core Activities

1. **react_agent_activity.py** - Reasoning and tool selection using DSPy
2. **tool_execution_activity.py** - Executes tools and updates trajectory
3. **extract_agent_activity.py** - Synthesizes final answers from trajectories
4. **find_events_activity.py** - Legacy activity for event finding (hardcoded tool)

### MCP Utilities (`activities/mcp_utils.py`)

Common utilities extracted for MCP activities:
- `get_user_display_name()` - Extract user names for personalization
- `get_mcp_server_config()` - Environment-based server configuration
- `call_mcp_tool()` - Generic MCP tool calling with error handling
- `parse_mcp_result()` - Parse MCP responses consistently
- `create_error_response()` - Standardized error responses

### MCP Architecture

- **Individual Services**: Separate MCP servers for forecast, historical, agricultural data
- **Unified Proxy**: Single endpoint (`mcp_proxy`) combining all services
- **Docker Profiles**: Use `weather_proxy` profile for unified access, `forecast` for individual services
- **Environment Configuration**: Services configured via environment variables

## Testing Strategy

- **Unit Tests** (`tests/`) - Test individual components in isolation
- **Integration Tests** (`integration_tests/`) - Test API endpoints with real Temporal backend
- **MCP Integration Tests** - Direct Python programs testing MCP client functionality
- **Proxy Integration Tests** - Test unified MCP proxy (not included in main test runner)
- Use markers (`-m api`, `-m workflow`) to run specific test categories
- Integration tests require services to be running via docker-compose

### MCP Proxy Testing

```bash
# Start weather proxy
./mcp_proxy/run_docker.sh

# Test proxy functionality
./mcp_proxy/test_docker.sh

# Run proxy integration tests
poetry run python integration_tests/test_proxy_integration.py

# Stop proxy
./mcp_proxy/stop_docker.sh
```

## Workflow Routing and Magic Words

The `SimpleAgentWorkflow` acts as a router for different reasoning patterns:
- Messages starting with "weather:" trigger the `AgenticAIWorkflow` as a child workflow
- This demonstrates how different query types can use different reasoning strategies
- Future enhancement: Use a classification agent to automatically select appropriate tool sets

## Important Notes

- Always ensure docker-compose services are running before integration tests
- The project uses Poetry for dependency management - avoid pip install
- Type hints are enforced - run `poetry run poe lint-types` before committing
- Frontend components (Phase 4) are not yet implemented
- The trajectory flow has been carefully designed to avoid double-writes (see trajectory-in-depth.md)
- Tool registry supports mock results for testing (`mock_results=True` by default)


## Critical Architecture Guidelines

### ⚠️ NEVER Mix Async and Sync Code

**ABSOLUTELY FORBIDDEN ANTI-PATTERNS:**
1. **DO NOT** create sync/async bridges or compatibility layers
2. **DO NOT** use `asyncio.run()` inside async functions or create nested event loops
3. **DO NOT** write sync wrappers around async code or vice versa
4. **DO NOT** attempt to "migrate" between sync and async patterns
5. **DO NOT** use threading to work around async/sync mismatches
6. **DO NOT** create legacy compatibility layers

**If you encounter a situation where mixing async/sync seems necessary:**
- **STOP IMMEDIATELY**
- **ASK THE USER** for clarification on the correct approach
- **EXPLAIN** why the anti-pattern is problematic
- **SUGGEST** proper async-only or sync-only alternatives

**Examples of what to avoid:**
```python
# ❌ NEVER DO THIS
def sync_wrapper(async_func):
    return asyncio.run(async_func())

# ❌ NEVER DO THIS
async def async_wrapper(sync_func):
    return await asyncio.to_thread(sync_func)

# ❌ NEVER DO THIS
class MixedAPI:
    def sync_method(self):
        return asyncio.run(self.async_method())
    
    async def async_method(self):
        return "data"
```

**Correct approach:**
- Choose either async OR sync for your entire component
- Use async libraries with async code (e.g., `httpx` instead of `requests`)
- Use sync libraries with sync code
- Keep clear boundaries between async and sync domains

This project uses **async patterns throughout** - maintain this consistency!