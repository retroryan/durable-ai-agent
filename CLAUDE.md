# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based distributed workflow application demonstrating durable AI conversation patterns using Temporal. The project uses FastAPI for the API server, Temporal for workflow orchestration, and Docker Compose for containerized deployment.

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

### Development Setup
```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
```

### Code Quality
```bash
poetry run poe format     # Format code with black and isort
poetry run poe lint       # Run all linters (black, isort, mypy)
poetry run poe lint-types # Run type checking only
```

### Testing
```bash
# Unit tests (no services required)
poetry run poe test

# Integration tests (requires docker-compose up)
docker-compose up -d
poetry run pytest integration_tests/ -v

# Test specific components
poetry run pytest integration_tests/ -m api -v
poetry run pytest integration_tests/ -m workflow -v
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
3. **Workflows** (`workflows/`) - Durable workflow definitions (SimpleAgentWorkflow)
4. **Activities** (`activities/`) - Atomic units of work with MCP integrations
5. **Tools** (`tools/`) - Reusable tool implementations (find_events)
6. **MCP Proxy** (`mcp_proxy/`) - Unified proxy server combining multiple weather services

### Key Design Patterns

- **Workflow Pattern**: Each conversation is a long-running Temporal workflow that maintains state
- **Message Processing**: Messages are processed through activities with automatic retry and error handling
- **Query Pattern**: Workflow state can be queried at any time without affecting execution
- **Signal Pattern**: New messages are sent to workflows via signals

### API Endpoints

- `POST /chat` - Start a new workflow with an initial message
- `GET /workflow/{workflow_id}/status` - Check workflow execution status
- `GET /workflow/{workflow_id}/query` - Query current workflow state

## Activities and MCP Integration

The project includes several Temporal activities that integrate with MCP (Model Context Protocol) servers:

### Available Activities

1. **weather_forecast_activity.py** - Calls forecast MCP server for weather predictions
2. **weather_historical_activity.py** - Calls historical MCP server for past weather data  
3. **agricultural_activity.py** - Calls agricultural MCP server for farming conditions
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
python integration_tests/test_proxy_integration.py

# Stop proxy
./mcp_proxy/stop_docker.sh
```

## Important Notes

- Always ensure docker-compose services are running before integration tests
- The project uses Poetry for dependency management - avoid pip install
- Type hints are enforced - run `poetry run poe lint-types` before committing
- Frontend components (Phase 4) are not yet implemented

## Code Quality Requirements

**ALWAYS run linting checks after implementing code changes:**
```bash
poetry run poe lint
```

If linting fails, fix the issues by:
1. Running `poetry run poe format` to auto-fix formatting issues
2. Addressing any type errors reported by mypy
3. Running `poetry run poe lint` again to verify all checks pass

This ensures the codebase maintains high quality standards and type safety.

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