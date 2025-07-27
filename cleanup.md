# Environment Variable Cleanup Recommendations

Based on a comprehensive analysis of environment variable usage across the codebase, here are recommendations for cleaning up and consolidating environment variables.

## Summary of Changes Made

1. **Consolidated worker.env into .env** - All worker-specific environment variables have been moved to the main .env file ✅
2. **Updated .env.example** - Created a comprehensive example file with all environment variables used across the project ✅
3. **Files that can be removed**:
   - `worker.env` - No longer needed as all variables are now in `.env`
   - `api.env` - Only contains redundant Temporal configuration already in `.env`

## Cleanup Status

### ✅ Completed
1. **TEMPORAL_HOST removed** - Standardized on TEMPORAL_ADDRESS throughout the codebase
2. **DSPY_PROVIDER → LLM_PROVIDER** - Completely replaced all occurrences:
   - Updated `shared/llm_utils.py`
   - Updated `.env` and `.env.example`
   - Updated `worker.env` (to be removed)
   - Updated `docs/DSPy Overview.md`
3. **Environment consolidation** - All variables now documented in `.env.example`
4. **Docker-compose review** - No api.env references found in docker-compose.yml

### ✅ All Tasks Completed
1. **Update scripts/run_api_local.sh** - Now uses `.env` and overrides TEMPORAL_ADDRESS for local development
2. **Update docs/LOCAL_API.md** - All references updated to use `.env`
3. **Fix shared/logging_config.py** - Changed LLM_BASE_URL to OLLAMA_BASE_URL

## Environment Variables Analysis

### Environment Variable Architecture

#### MCP_URL vs MCP_PROXY_URL Clarification
- **MCP_PROXY_URL**: Used by the `mcp_proxy/` service to route requests to multiple MCP servers (`mcp_servers/`) in Docker Compose. This is the internal Docker service URL (`http://weather-proxy:8000/mcp`)
- **MCP_URL**: The general MCP endpoint URL used by worker and other services. In proxy mode, this is the same as MCP_PROXY_URL for Docker environments, or `http://localhost:8001/mcp` for local development
- **Purpose**: The proxy consolidates multiple weather services (forecast, historical, agricultural) into a single endpoint, simplifying configuration and client usage

#### Variables Used by API Server and Worker (from shared/config.py)
**API Server uses:**
- `TEMPORAL_ADDRESS` - Temporal server connection
- `TEMPORAL_NAMESPACE` - Temporal namespace
- `API_HOST` - API server host binding
- `API_PORT` - API server port
- `API_URL` - Full API URL (used for external references)
- `LOG_LEVEL` - Logging configuration

**Worker uses:**
- `TEMPORAL_ADDRESS` - Temporal server connection
- `TEMPORAL_NAMESPACE` - Temporal namespace  
- `WORKER_TASK_QUEUE` - Task queue name
- `MCP_PROXY_MODE` - Whether to use proxy or direct MCP connections
- `MCP_PROXY_URL` - MCP proxy endpoint
- `LOG_LEVEL` - Logging configuration

**Authentication (optional for both):**
- `TEMPORAL_TLS_CERT` - mTLS certificate path
- `TEMPORAL_TLS_KEY` - mTLS private key path
- `TEMPORAL_API_KEY` - API key authentication

### Unused or Potentially Redundant Variables

1. **API_SERVER** (in api.env)
   - Not found in any Python code
   - **Recommendation**: Remove

2. **VITE_API_TIMEOUT** (in .env)
   - Only relevant for frontend, not used in backend code
   - **Recommendation**: Keep but document it's frontend-only

3. **LLM_BASE_URL** (referenced in shared/logging_config.py)
   - Should be **OLLAMA_BASE_URL** based on actual usage
   - **Recommendation**: Fix the reference in logging_config.py

4. **Multiple MCP server configuration variables**
   - Many MCP_*_SERVER_HOST/PORT/URL variables when using proxy mode
   - **Recommendation**: Document that these are only needed for direct mode

### Variables Missing from .env.example (now added)

- DEMO_DEBUG
- DSPY_DEBUG
- TEMPORAL_TLS_CERT
- TEMPORAL_TLS_KEY
- TEMPORAL_API_KEY
- MCP_PORT
- STRIPE_API_KEY

## Recommended Actions

### 1. Immediate Cleanup

```bash
# Remove redundant files
rm worker.env
rm api.env

# Update docker-compose.yml to use only .env
# (worker service already uses .env, so no changes needed)
```

### 2. ✅ All Code Updates Completed

All necessary code updates have been completed:
- **shared/logging_config.py** - Fixed LLM_BASE_URL → OLLAMA_BASE_URL
- **scripts/run_api_local.sh** - Updated to use .env with local overrides
- **docs/LOCAL_API.md** - Documentation updated to reference .env

### 3. Documentation Updates

Update README.md and other documentation to:
- Reference only `.env` file (not worker.env)
- Clarify when to use proxy mode vs direct mode for MCP
- Explain the difference between MCP_URL and MCP_PROXY_URL

### 4. Environment Variable Best Practices

1. **Group related variables** - ✅ Already done in .env.example with clear sections
2. **Use consistent naming** - ✅ Standardized on TEMPORAL_ADDRESS (removed TEMPORAL_HOST)
3. **Document required vs optional** - Add comments indicating which are required
4. **Avoid duplication** - ✅ Consolidating to one .env file for all services
5. **Secure sensitive data** - ✅ .env is gitignored (already following this)

## Security Note

The `.env` file is properly included in `.gitignore`, so API keys and other sensitive information remain local and are not committed to version control. This is the correct security practice.

## Migration Steps

1. Back up current environment files
2. Copy `.env.example` to `.env` and fill in your actual values
3. Remove `worker.env` and `api.env`
4. Update any scripts or documentation that reference the old files
5. Test all services to ensure they still work with consolidated configuration

## Future Improvements

1. Consider using a configuration management tool for different environments (dev, staging, prod)
2. Implement environment variable validation on startup
3. Add a script to check for missing required environment variables
4. Consider using Docker secrets for sensitive values instead of environment variables