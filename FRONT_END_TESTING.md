# Frontend Testing and Timeout Configuration

This document describes the timeout configuration for frontend API requests and how to adjust them for testing long-running operations.

## Overview

The frontend application has a multi-layer timeout configuration:
1. **Frontend JavaScript client** - Controls browser-side request timeouts
2. **Nginx reverse proxy** - Controls proxy timeouts between frontend and API
3. **Uvicorn API server** - Controls server-side connection timeouts

## Current Timeout Settings

### 1. Frontend JavaScript Client (60 seconds default)
- **Location**: `frontend/src/services/api.js`
- **Default**: 60000ms (60 seconds)
- **Configuration**: Via `VITE_API_TIMEOUT` environment variable
- **Implementation**: Uses AbortController API to cancel requests

### 2. Nginx Proxy (120 seconds)
- **Location**: `frontend/nginx.conf`
- **Settings**:
  - `proxy_connect_timeout`: 120s
  - `proxy_send_timeout`: 120s
  - `proxy_read_timeout`: 120s
- **Applied to**: All API routes (`/chat`, `/workflow/*`, `/health`)

### 3. Uvicorn Server (120 seconds)
- **Location**: `Dockerfile.api`
- **Setting**: `--timeout-keep-alive 120`
- **Purpose**: Keeps connections alive for long-running requests

## How to Adjust Timeouts

### Option 1: Environment Variable (Recommended for Testing)

Set the timeout in your `.env` file (milliseconds):
```bash
# Set to 3 minutes
VITE_API_TIMEOUT=180000
```

Then rebuild the frontend:
```bash
docker-compose build frontend
docker-compose up -d frontend
```

### Option 2: Per-Request Timeout

Pass a custom timeout to any API call:
```javascript
// 90-second timeout for this specific request
await api.sendMessage(message, workflowId, userName, 90000);
await api.getStatus(workflowId, 90000);
await api.queryWorkflow(workflowId, 90000);
```

### Option 3: Modify Default Configurations

#### Frontend Default Timeout
Edit `frontend/src/services/api.js`:
```javascript
// Change from 60000 to your desired timeout (in milliseconds)
const DEFAULT_TIMEOUT = import.meta.env.VITE_API_TIMEOUT ? parseInt(import.meta.env.VITE_API_TIMEOUT) : 180000;
```

#### Nginx Proxy Timeouts
Edit `frontend/nginx.conf` (all proxy locations):
```nginx
proxy_connect_timeout 180s;
proxy_send_timeout 180s;
proxy_read_timeout 180s;
```

#### Uvicorn Server Timeout
Edit `Dockerfile.api`:
```dockerfile
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "180"]
```

## Applying Changes

After making configuration changes:

```bash
# Stop all services
docker-compose down

# Rebuild affected services
docker-compose build api frontend

# Start services
docker-compose up -d
```

## Testing Long-Running Operations

### Example: Testing Weather Queries with Extended Timeouts

1. Set environment variable in `.env`:
   ```bash
   VITE_API_TIMEOUT=180000  # 3 minutes
   ```

2. Rebuild and restart:
   ```bash
   docker-compose build frontend
   docker-compose up -d
   ```

3. Test with a complex weather query:
   ```
   weather: Give me detailed forecast for Seattle, historical data for the past month, and agricultural recommendations
   ```

### Monitoring Timeouts

Check logs to see if timeouts are occurring:

```bash
# Frontend nginx logs
docker logs durable-ai-agent-frontend

# API server logs
docker logs durable-ai-agent-api

# Worker logs (for Temporal activity timeouts)
docker logs temporal-ai-agent-worker
```

## Common Timeout Issues

### Issue 1: Request times out before completion
**Symptom**: "Request timeout after 60000ms" error
**Solution**: Increase `VITE_API_TIMEOUT` environment variable

### Issue 2: Nginx returns 504 Gateway Timeout
**Symptom**: 504 error after 30 seconds (or configured proxy timeout)
**Solution**: Ensure Nginx proxy timeouts are >= frontend timeout

### Issue 3: Connection drops during long operations
**Symptom**: Connection reset or dropped
**Solution**: Increase Uvicorn `--timeout-keep-alive` setting

### Issue 4: Temporal activity timeout
**Symptom**: Workflow fails with activity timeout error
**Solution**: This requires modifying Temporal activity timeout in `workflows/simple_agent_workflow.py`

## Timeout Chain Summary

For a request to complete successfully, all timeouts in the chain must be sufficient:

1. **Frontend JavaScript**: Default 60s (configurable via `VITE_API_TIMEOUT`)
2. **Nginx Proxy**: 120s (all proxy timeouts)
3. **Uvicorn Server**: 120s keep-alive
4. **Temporal Activities**: 30s (configured in workflow definitions)

The most restrictive timeout in the chain will determine when a request fails.

## Best Practices

1. **Development**: Use longer timeouts (2-3 minutes) for testing complex operations
2. **Production**: Balance between user experience and operation completion
3. **Monitoring**: Log timeout occurrences to identify operations that need optimization
4. **User Feedback**: Show progress indicators for long-running operations

## Quick Reference

```bash
# Check current timeout settings
grep -r "timeout" frontend/src/services/api.js
grep -r "timeout" frontend/nginx.conf
grep "timeout" Dockerfile.api

# View logs for timeout issues
docker-compose logs -f api frontend worker

# Test with custom timeout (in frontend code)
api.sendMessage("weather: complex query", null, "TestUser", 180000)
```