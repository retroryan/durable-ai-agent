# LLM Mistakes and Mitigations

This document tracks common mistakes made by LLMs when using the agentic loop system and proposed solutions.

## 1. Hallucinating Tool Parameters

### Error Description
When running the agentic_loop demo, the LLM may hallucinate parameters that don't exist for tools, causing runtime errors.

**Example Error:**
```
2025-07-21 20:51:13 - __main__ - ERROR - Tool execution error: WeatherForecastTool.execute() got an unexpected keyword argument 'data_fields'
TypeError: WeatherForecastTool.execute() got an unexpected keyword argument 'data_fields'
```

### Root Cause
The LLM attempts to pass a `data_fields` parameter to the `get_weather_forecast` tool, which only accepts:
- `location` (optional string)
- `latitude` (optional float)
- `longitude` (optional float)  
- `days` (int, default 7)

This happens because the LLM is trying to be helpful by filtering data fields, but the tool doesn't support this functionality.

### Proposed Solutions

#### Solution 1: Parameter Validation (Recommended)
Add parameter validation in the demo script to filter out invalid arguments before calling tools:

```python
# In demo_react_agent.py, before tool.execute():
import inspect

# Get the tool's execute method signature to filter valid args
sig = inspect.signature(tool.execute)
valid_params = set(sig.parameters.keys()) - {'self'}

# Filter tool_args to only include valid parameters
tool_args = trajectory.tool_args.copy()
filtered_args = {k: v for k, v in tool_args.items() if k in valid_params}

# Log if any args were filtered out
filtered_out = set(tool_args.keys()) - set(filtered_args.keys())
if filtered_out:
    logger.warning(f"Filtered out invalid arguments for {trajectory.tool_name}: {filtered_out}")

# Use filtered_args instead of tool_args
trajectory.observation = tool.execute(**filtered_args)
```

#### Solution 2: Enhanced Prompt Engineering
Update the `AgricultureReactSignature` to explicitly list valid parameters:

```python
class AgricultureReactSignature(dspy.Signature):
    """Weather tool execution requirements...
    
    WEATHER TOOL PARAMETERS (use ONLY these):
    - get_weather_forecast: latitude (float), longitude (float), days (int, 1-16)
    - get_historical_weather: latitude (float), longitude (float), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD)
    - get_agricultural_conditions: latitude (float), longitude (float), crop_type (string), days (int)
    
    IMPORTANT: Do NOT invent additional parameters like 'data_fields' or 'location'. 
    Use ONLY the parameters listed above for each tool.
    """
```

#### Solution 3: Tool Documentation
Add parameter documentation to each tool's description:

```python
class WeatherForecastTool(MCPTool):
    description: str = (
        "Get weather forecast for a location. "
        "Parameters: latitude (float), longitude (float), days (int 1-16). "
        "Do not use any other parameters."
    )
```

### Recommended Approach
Implement Solution 1 (parameter validation) as a defensive programming measure, combined with Solution 2 (enhanced prompts) for better LLM guidance. This provides both prevention and protection against parameter hallucination.

### Testing
After implementing the fix, test with:
```bash
MCP_USE_PROXY=false poetry run python agentic_loop/demo_react_agent.py agriculture
```

The demo should handle invalid parameters gracefully and log warnings when they are filtered out.