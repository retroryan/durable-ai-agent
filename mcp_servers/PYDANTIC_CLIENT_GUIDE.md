# FastMCP Client Pydantic Integration Guide

This guide demonstrates how to properly use Pydantic models when building FastMCP clients that interact with MCP servers. Using Pydantic models provides type safety, automatic validation, and better developer experience.

## Table of Contents
1. [Overview](#overview)
2. [Key Concepts](#key-concepts)
3. [Setting Up Pydantic Models](#setting-up-pydantic-models)
4. [Creating Model Instances](#creating-model-instances)
5. [Calling Tools with Pydantic Models](#calling-tools-with-pydantic-models)
6. [Handling Validation](#handling-validation)
7. [Advanced Patterns](#advanced-patterns)
8. [Best Practices](#best-practices)

## Overview

FastMCP clients can directly use Pydantic models as arguments when calling server tools. This approach provides:
- **Type Safety**: Full typing support in your IDE
- **Automatic Validation**: Pydantic validates data before sending to the server
- **Automatic Serialization**: FastMCP handles converting models to JSON
- **Better Developer Experience**: Work with Python objects instead of raw dictionaries

## Key Concepts

### 1. Model Import Pattern
When building a client, you need access to the same Pydantic models that the server uses:

```python
# Import the Pydantic models from the server
try:
    from models import ForecastRequest
except ImportError:
    # If running from a different directory
    from mcp_servers.models import ForecastRequest
```

### 2. Server-Client Contract
The server defines tools that expect Pydantic models:
```python
@server.tool
async def get_weather_forecast(request: ForecastRequest) -> dict:
    """Server expects a ForecastRequest Pydantic model"""
    ...
```

The client must provide arguments that match this contract.

## Setting Up Pydantic Models

### Basic Model Definition
Here's an example from our forecast server's models:

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional

class ForecastRequest(BaseModel):
    """Request model for weather forecast tool."""
    location: Optional[str] = Field(
        None, 
        description="Location name (e.g., 'Chicago, IL')"
    )
    latitude: Optional[float] = Field(
        None, 
        description="Direct latitude (-90 to 90)"
    )
    longitude: Optional[float] = Field(
        None, 
        description="Direct longitude (-180 to 180)"
    )
    days: int = Field(
        default=7,
        ge=1,
        le=16,
        description="Number of forecast days (1-16)"
    )
    
    @model_validator(mode='after')
    def check_at_least_one_location(self):
        """Ensure at least one location method is provided."""
        has_location = self.location is not None
        has_coords = self.latitude is not None and self.longitude is not None
        if not has_location and not has_coords:
            raise ValueError('Either location name or coordinates required')
        return self
```

## Creating Model Instances

### Basic Usage
From `sample_client.py`, here's how to create Pydantic model instances:

```python
# Create a model with location name
request1 = ForecastRequest(location="San Francisco", days=1)

# Create a model with coordinates (faster than geocoding)
coords_request = ForecastRequest(
    latitude=40.7128,  # NYC coordinates
    longitude=-74.0060,
    days=2
)

# Using defaults - days defaults to 7
london_request = ForecastRequest(location="London")
```

### Validation at Creation Time
Pydantic validates data when you create the model instance:

```python
# This will raise a validation error immediately
try:
    invalid_request = ForecastRequest(days=3)  # Missing required location
except Exception as e:
    print(f"✓ Caught expected error for missing location: {e}")
    # Output: Either location name or coordinates (latitude, longitude) required

# This will be clamped to valid range (1-16)
paris_request = ForecastRequest(location="Paris", days=20)  # days will be clamped to 16
```

## Calling Tools with Pydantic Models

### The Correct Pattern
When calling tools, pass the Pydantic model instance directly:

```python
async def test_forecast_server():
    client = Client("http://localhost:7778/mcp")
    
    async with client:
        # Create a Pydantic model instance
        request = ForecastRequest(location="San Francisco", days=1)
        
        # Pass the model directly - FastMCP will serialize it
        result = await client.call_tool("get_weather_forecast", {"request": request})
        
        # Handle the response
        if result and hasattr(result[0], 'text'):
            data = json.loads(result[0].text)
            print(f"Weather: {json.dumps(data, indent=2)}")
```

### Multiple Examples from sample_client.py

```python
# Example 1: Simple location-based request
request1 = ForecastRequest(location="San Francisco", days=1)
result = await client.call_tool("get_weather_forecast", {"request": request1})

# Example 2: Multi-day forecast
london_request = ForecastRequest(location="London", days=3)
result = await client.call_tool("get_weather_forecast", {"request": london_request})

# Example 3: Using coordinates for better performance
coords_request = ForecastRequest(
    latitude=40.7128,  # NYC coordinates
    longitude=-74.0060,
    days=2
)
result = await client.call_tool("get_weather_forecast", {"request": coords_request})
```

## Handling Validation

### Client-Side Validation
Pydantic validates data before it's sent to the server:

```python
# Test with missing required parameters
try:
    # This fails at model creation, not at tool call
    invalid_request = ForecastRequest(days=3)  # Missing location
except ValueError as e:
    print(f"Validation error: {e}")
    # Handle the validation error appropriately
```

### Server Response Handling
The server returns data that needs to be parsed:

```python
# The response is typically a list of TextContent objects
if result and hasattr(result[0], 'text'):
    # Parse the JSON response
    data = json.loads(result[0].text)
    
    # Access the structured data
    print(f"Location: {data['location_info']['name']}")
    print(f"Current temp: {data['current']['temperature_2m']}°C")
    print(f"Humidity: {data['current']['relative_humidity_2m']}%")
```

## Advanced Patterns

### 1. Using Field Validators
The ForecastRequest model includes field validators that handle edge cases:

```python
@field_validator('latitude')
@classmethod
def validate_latitude(cls, v):
    """Validate latitude is within valid range."""
    if v is not None and not -90 <= v <= 90:
        raise ValueError(f'Latitude must be between -90 and 90, got {v}')
    return v
```

### 2. Model Validators
Model-level validation ensures business rules:

```python
@model_validator(mode='after')
def check_at_least_one_location(self):
    """Ensure at least one location method is provided."""
    has_location = self.location is not None
    has_coords = self.latitude is not None and self.longitude is not None
    if not has_location and not has_coords:
        raise ValueError('Either location name or coordinates required')
    return self
```

### 3. Working with Optional Fields
The model supports multiple ways to specify location:

```python
# Option 1: Location name (requires geocoding)
by_name = ForecastRequest(location="Chicago, IL", days=3)

# Option 2: Coordinates (faster, no geocoding needed)
by_coords = ForecastRequest(latitude=41.8781, longitude=-87.6298, days=3)

# Option 3: Both (coordinates take precedence)
both = ForecastRequest(
    location="Chicago",  # Used for display name
    latitude=41.8781,
    longitude=-87.6298,
    days=3
)
```

## Best Practices

### 1. Import Models Properly
Always import the same models the server uses:
```python
# Good: Import from shared location
from models import ForecastRequest

# Bad: Redefining models in the client
class MyForecastRequest(BaseModel):  # Don't do this!
    ...
```

### 2. Handle Validation Errors
Always wrap model creation in try-except when using user input:
```python
try:
    request = ForecastRequest(
        location=user_input_location,
        days=user_input_days
    )
except ValueError as e:
    print(f"Invalid input: {e}")
    # Provide user-friendly error message
```

### 3. Use Type Hints
Leverage type hints for better IDE support:
```python
async def get_forecast(location: str, days: int = 7) -> dict:
    """Type-safe function that creates and uses Pydantic models."""
    request: ForecastRequest = ForecastRequest(location=location, days=days)
    
    async with Client("http://localhost:7778/mcp") as client:
        result = await client.call_tool("get_weather_forecast", {"request": request})
        # ... handle response
```

### 4. Prefer Coordinates When Available
As noted in the model documentation, using coordinates is faster:
```python
# Faster: Direct coordinates (no geocoding required)
fast_request = ForecastRequest(latitude=37.7749, longitude=-122.4194, days=1)

# Slower: Location name (requires geocoding API call)
slow_request = ForecastRequest(location="San Francisco", days=1)
```

### 5. Test Edge Cases
Always test validation boundaries:
```python
# Test validation limits
edge_cases = [
    ForecastRequest(location="Paris", days=1),    # Minimum days
    ForecastRequest(location="Paris", days=16),   # Maximum days
    ForecastRequest(location="Paris", days=20),   # Should be clamped to 16
    ForecastRequest(latitude=90, longitude=180),  # Edge coordinates
]
```

## Complete Example

Here's a complete example combining all the patterns:

```python
import asyncio
import json
from fastmcp import Client
from models import ForecastRequest

async def get_weather_smartly(location_input: str | tuple[float, float], days: int = 3):
    """
    Get weather forecast using either location name or coordinates.
    
    Args:
        location_input: Either a string location name or (lat, lon) tuple
        days: Number of forecast days (1-16)
    """
    # Create the appropriate request based on input type
    if isinstance(location_input, str):
        request = ForecastRequest(location=location_input, days=days)
        print(f"Getting {days}-day forecast for {location_input}")
    else:
        lat, lon = location_input
        request = ForecastRequest(latitude=lat, longitude=lon, days=days)
        print(f"Getting {days}-day forecast for coordinates ({lat}, {lon})")
    
    # Connect to the MCP server
    client = Client("http://localhost:7778/mcp")
    
    async with client:
        try:
            # Call the tool with the Pydantic model
            result = await client.call_tool("get_weather_forecast", {"request": request})
            
            # Parse and return the response
            if result and hasattr(result[0], 'text'):
                data = json.loads(result[0].text)
                return {
                    "location": data['location_info']['name'],
                    "current_temp": data['current']['temperature_2m'],
                    "summary": data['summary']
                }
        except Exception as e:
            print(f"Error getting forecast: {e}")
            return None

# Usage examples
async def main():
    # By location name
    result1 = await get_weather_smartly("New York", days=3)
    
    # By coordinates (faster)
    result2 = await get_weather_smartly((40.7128, -74.0060), days=5)
    
    print(result1)
    print(result2)

if __name__ == "__main__":
    asyncio.run(main())
```

## Summary

Using Pydantic models with FastMCP clients provides:
1. **Type safety** at development time
2. **Automatic validation** before sending requests
3. **Clean, readable code** with proper Python objects
4. **Better error handling** with descriptive validation messages
5. **Consistency** between client and server contracts

By following these patterns, you can build robust, type-safe MCP clients that are easy to maintain and debug.