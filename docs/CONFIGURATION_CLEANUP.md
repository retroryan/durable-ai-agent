# Configuration Cleanup Summary

This document explains the configuration changes made to simplify the project and ensure everything runs properly with `run_docker.sh`.

## Changes Made

### 1. Unified Docker Execution
- **Changed**: `run_docker.sh` now always runs ALL services (removed `--run_client` flag)
- **Why**: Simplifies operations - one command runs everything needed for the demo
- **Result**: No more confusion about which services are running where

### 2. Removed Local API Execution
- **Removed**: `api/config.py` and `scripts/run_api_local.sh`
- **Changed**: API now uses `Settings` from `shared/config.py`
- **Why**: Eliminates the localhost vs Docker networking confusion that caused MCP connection failures
- **Result**: Consistent networking - all services run in Docker and can communicate properly

### 3. Fixed MCP Server URL Configuration
- **Changed**: `.env` now has `MCP_SERVER_URL=http://mcp-server:7778/mcp` (was `http://localhost:7778/mcp`)
- **Kept**: `docker-compose.yml` still explicitly sets `MCP_SERVER_URL=http://mcp-server:7778/mcp` for the worker
- **Why**: 
  - The `.env` value now matches what's needed for Docker networking
  - Keeping it in docker-compose.yml provides explicit documentation
  - No conflicts since both have the same value
- **Result**: Worker can properly connect to MCP server using Docker service names

## How It Works Now

1. **Starting Services**: Run `./run_docker.sh` - starts everything in Docker
2. **Networking**: All services communicate via Docker network using service names:
   - API → Temporal: `temporal:7233`
   - Worker → Temporal: `temporal:7233`
   - Worker → MCP Server: `mcp-server:7778`
3. **Port Mappings** (for external access):
   - API: `localhost:8000`
   - Frontend: `localhost:3000`
   - Temporal UI: `localhost:8080`
   - MCP Server: `localhost:7778`

## Integration Testing

Integration tests run locally but connect to services in Docker:
```bash
# Start all services
./run_docker.sh

# Run tests (connects to localhost:8000 which maps to API in Docker)
poetry run python integration_tests/test_api_e2e.py
```

## Key Principle

Everything runs in Docker for consistency. The previous setup mixed local and Docker execution, which caused networking issues. Now:
- All services run in Docker
- Services communicate using Docker service names
- External access uses localhost port mappings
- No more localhost vs Docker network confusion