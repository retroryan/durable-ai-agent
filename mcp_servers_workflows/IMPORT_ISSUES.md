# Temporal Workflow Import Issues in MCP Servers

## Summary

We encountered import restrictions when trying to implement Temporal workflows within the `mcp_servers` package. The Temporal workflow sandbox enforces strict import controls to ensure workflow determinism, which conflicted with the package structure.

## The Problem

### 1. Workflow Sandbox Restrictions

Temporal's workflow sandbox restricts certain imports to ensure workflows are deterministic. The specific error we encountered was:

```
temporalio.worker.workflow_sandbox._restrictions.RestrictedWorkflowAccessError: 
Cannot access urllib.request.Request.__mro_entries__ from inside a workflow.
```

This error occurred because:
- The workflow was defined inside the `mcp_servers` package
- The package's `__init__.py` or other modules imported `httpx` (via `utils/api_client.py`)
- Even though the workflow itself didn't use these imports, Python's module loading mechanism triggered them
- The workflow sandbox detected these restricted imports during validation

### 2. Package Structure Issues

The `mcp_servers` package structure:
```
mcp_servers/
├── __init__.py
├── agricultural_server.py
├── weather_workflows.py      # Workflows here trigger package imports
├── weather_activity.py
└── utils/
    ├── __init__.py
    ├── api_client.py         # Imports httpx
    └── weather_utils.py
```

When Python imports `mcp_servers.weather_workflows`, it first processes:
1. `mcp_servers/__init__.py`
2. Any imports in that file or related modules
3. This includes `utils/api_client.py` which imports `httpx`

### 3. Why the Reference Implementation Works

The [temporal-durable-mcp-weather-sample](https://github.com/Aslan11/temporal-durable-mcp-weather-sample) works because:
- All files are in the root directory (no package structure)
- No `__init__.py` files that might trigger additional imports
- Clean separation between workflows and modules with restricted imports

## Attempted Solutions

### 1. Wrapping Imports with `workflow.unsafe.imports_passed_through()`
- Tried wrapping activity imports in the workflow
- Tried wrapping all imports at module level
- Still failed because package initialization happens before the wrapper takes effect

### 2. Using String References for Activities
- Changed from importing activities to using string names
- This helped avoid direct imports but didn't solve the package initialization issue

### 3. Cleaning Package `__init__.py`
- Removed imports from `mcp_servers/__init__.py`
- Still failed because `utils/__init__.py` and module dependencies were processed

## The Fundamental Issue

The core problem is that Temporal workflows must be in modules that have absolutely no import chain leading to restricted modules like `httpx`, `urllib`, etc. When workflows are inside a package that contains MCP server code (which needs these modules), it creates an irreconcilable conflict.

## Solutions

### Option 1: Separate Workflow Package (Recommended)
Move workflows to a completely separate package/directory with no dependencies on restricted modules:
```
workflows/
├── weather_workflows.py     # Only imports temporalio
activities/
├── weather_activity.py      # Can import anything
mcp_servers/
├── agricultural_server.py   # Uses workflows via Temporal client
```

### Option 2: Direct Implementation (Current Reversion)
Have MCP servers call weather utilities directly without Temporal workflows. This loses durability but avoids all import issues.

### Option 3: Standalone Services
Run workflows as a completely separate service that MCP servers communicate with via Temporal client only.

## Key Learnings

1. **Temporal workflows must be in "pure" modules** - No import chains to restricted modules
2. **Package structure matters** - Being inside a package triggers all package imports
3. **String activity references aren't enough** - The module itself must load cleanly
4. **Separation of concerns is critical** - Workflows should be isolated from implementation details

## Conclusion

While Temporal workflows provide excellent durability and observability, integrating them within an existing package structure (especially one that uses HTTP clients) requires careful architectural planning. The cleanest approach is complete separation of workflow definitions from implementation code.