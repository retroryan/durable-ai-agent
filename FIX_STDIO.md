# FIX_STDIO.md - Stdio MCP Implementation Architecture

## Status: ✅ Implemented

The stdio client integration test (`integration_tests/test_stdio_client.py`) passes successfully. The MCPClientManager correctly handles stdio connections. This document describes the architecture for stdio support in the agentic_loop demo.

## Architecture Overview

### Current State
- **MCPClientManager**: Fully supports stdio connections with connection pooling
- **Test Coverage**: All stdio functionality tested and passing
- **Integration Points**: Ready for integration with agentic_loop demo

### Implementation Approach

The implementation follows these principles:
1. **Simplicity First**: Minimal changes to existing code
2. **Demo-Focused**: Optimized for agentic_loop standalone usage
3. **No Backwards Compatibility**: Clean implementation without legacy support
4. **Environment-Based Configuration**: Simple toggle via environment variables

## Design Decisions

### 1. Scope Limitation
- Stdio support is implemented specifically for the agentic_loop demo
- No changes to the main Temporal workflow system
- Tools continue to use the existing async activity pattern in production

### 2. Configuration Strategy
- Single environment variable (`MCP_USE_STDIO`) toggles between HTTP and stdio
- Server paths are resolved relative to the demo script location
- No complex configuration or multiple deployment modes

### 3. Tool Architecture
- MCP tools remain unchanged - they continue to raise errors in `execute()`
- All MCP execution happens through the async activity system
- The `get_mcp_config()` method handles both HTTP and stdio transparently

## Implementation Details

### Environment Configuration
The agentic_loop demo uses a local `.env` file with:
- `MCP_USE_STDIO`: Enable/disable stdio mode
- Server path resolution based on project structure
- No Docker or complex deployment configuration

### Path Resolution
- Server scripts are located in `mcp_servers/` directory
- Paths are resolved relative to the project root
- The demo script handles path construction automatically

### Connection Management
- MCPClientManager handles both HTTP and stdio connections
- Connection pooling works identically for both transport types
- Clean shutdown of stdio processes on completion

## Benefits

1. **Development Simplicity**: Run demos without Docker or HTTP servers
2. **Fast Iteration**: Direct process communication for quick testing
3. **Debugging**: Easier to debug with direct process output
4. **Portability**: Works on any system with Python installed

## Usage

The agentic_loop demo automatically detects stdio configuration from environment:
```bash
# Use stdio mode
MCP_USE_STDIO=true poetry run python agentic_loop/demo_react_agent.py agriculture

# Use HTTP mode (default)
poetry run python agentic_loop/demo_react_agent.py agriculture
```