#!/usr/bin/env python3
"""
Sample MCP client for testing the forecast server.
Uses FastMCP client library to connect and call tools.

This demonstrates the correct async-only patterns for FastMCP clients.
"""

import asyncio
import json
from fastmcp import Client
from fastmcp.exceptions import ToolError

# Import the Pydantic models from the server
try:
    from models import ForecastRequest
except ImportError:
    # If running from a different directory
    from mcp_servers.models import ForecastRequest


async def test_forecast_server_http():
    """Test the forecast server using HTTP transport."""
    print("\n--- Testing with HTTP Transport ---")
    
    # Connect to the HTTP endpoint
    client = Client("http://localhost:7778/mcp")
    
    async with client:
        print("Connected to forecast server via HTTP!")
        
        # Verify connection with ping
        try:
            is_healthy = await client.ping()
            if is_healthy:
                print("✓ Server is healthy and responsive")
        except Exception as e:
            print(f"⚠️  Ping failed: {e}")
        
        # List available tools
        tools = await client.list_tools()
        print("\nAvailable tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                props = tool.inputSchema.get('properties', {})
                if props:
                    print(f"    Parameters: {json.dumps(props, indent=6)}")
        
        # Test get_weather_forecast tool
        print("\n--- Testing get_weather_forecast ---")
        try:
            # Create a Pydantic model instance
            request1 = ForecastRequest(location="San Francisco", days=1)
            
            # Pass the Pydantic model directly - FastMCP will serialize it
            result = await client.call_tool("get_weather_forecast", {"request": request1})
            
            # Result is a list of TextContent objects
            if result and hasattr(result[0], 'text'):
                data = json.loads(result[0].text)
                print(f"Weather in San Francisco: {json.dumps(data, indent=2)}")
            else:
                print(f"Weather in San Francisco: {result}")
            
            # Test another location with Pydantic model
            request2 = ForecastRequest(location="New York", days=1)
            result2 = await client.call_tool("get_weather_forecast", {"request": request2})
            
            if result2 and hasattr(result2[0], 'text'):
                data2 = json.loads(result2[0].text)
                print(f"\nWeather in New York: {json.dumps(data2, indent=2)}")
            else:
                print(f"\nWeather in New York: {result2}")
        except ToolError as e:
            print(f"Error calling get_weather_forecast: {e}")
        
        # Test multi-day forecasts
        print("\n--- Testing multi-day forecasts ---")
        try:
            # Create Pydantic model for London
            london_request = ForecastRequest(location="London", days=3)
            result = await client.call_tool(
                "get_weather_forecast",
                {"request": london_request}
            )
            if result and hasattr(result[0], 'text'):
                data = json.loads(result[0].text)
                print(f"3-day forecast for London: {json.dumps(data, indent=2)}")
            else:
                print(f"3-day forecast for London: {result}")
            
            # Test with different parameters
            tokyo_request = ForecastRequest(location="Tokyo", days=5)
            result2 = await client.call_tool(
                "get_weather_forecast",
                {"request": tokyo_request}
            )
            if result2 and hasattr(result2[0], 'text'):
                data2 = json.loads(result2[0].text)
                print(f"\n5-day forecast for Tokyo: {json.dumps(data2, indent=2)}")
            else:
                print(f"\n5-day forecast for Tokyo: {result2}")
        except ToolError as e:
            print(f"Error calling get_weather_forecast: {e}")
        
        # Test edge cases
        print("\n--- Testing edge cases ---")
        try:
            # Test with invalid days (should be clamped to 1-7)
            paris_request = ForecastRequest(location="Paris", days=10)  # Should be clamped to 7
            result = await client.call_tool(
                "get_weather_forecast",
                {"request": paris_request}
            )
            if result and hasattr(result[0], 'text'):
                data = json.loads(result[0].text)
                print(f"Forecast with days=10 (should be clamped): {json.dumps(data, indent=2)}")
            else:
                print(f"Forecast with days=10 (should be clamped): {result}")
        except ToolError as e:
            print(f"Error with edge case: {e}")
        
        # Test using coordinates with Pydantic model
        print("\n--- Testing with coordinates (Pydantic validation) ---")
        try:
            # Using coordinates instead of location name (faster)
            coords_request = ForecastRequest(
                latitude=40.7128,  # NYC coordinates
                longitude=-74.0060,
                days=2
            )
            result = await client.call_tool(
                "get_weather_forecast",
                {"request": coords_request}
            )
            if result and hasattr(result[0], 'text'):
                data = json.loads(result[0].text)
                print(f"Weather by coordinates: {data['location_info']['name']} ({data['location_info']['coordinates']['latitude']}, {data['location_info']['coordinates']['longitude']})")
                print(f"Current temp: {data['current']['temperature_2m']}°C")
        except Exception as e:
            print(f"Error with coordinates: {e}")


async def test_with_callbacks():
    """Test client with callback handlers."""
    print("\n\n--- Testing with Callback Handlers ---")
    
    # Define callback handlers
    async def log_handler(message):
        print(f"[Server Log] {message.level}: {message.data}")
    
    async def progress_handler(progress, total, msg):
        if total:
            print(f"[Progress] {progress}/{total} - {msg}")
        else:
            print(f"[Progress] {progress} - {msg}")
    
    # Create client with handlers
    client = Client(
        "http://localhost:7778/mcp",
        log_handler=log_handler,
        progress_handler=progress_handler
    )
    
    async with client:
        print("Connected with callback handlers!")
        
        # Make a call that might trigger callbacks
        seattle_request = ForecastRequest(location="Seattle", days=7)
        result = await client.call_tool("get_weather_forecast", {
            "request": seattle_request
        })
        if result and hasattr(result[0], 'text'):
            data = json.loads(result[0].text)
            print(f"\n7-day forecast for Seattle: {json.dumps(data, indent=2)}")
        else:
            print(f"\n7-day forecast for Seattle: {result}")


async def test_error_handling():
    """Test robust error handling patterns."""
    print("\n\n--- Testing Error Handling ---")
    
    client = Client("http://localhost:7778/mcp")
    
    async with client:
        # Test with invalid parameters
        try:
            result = await client.call_tool(
                "get_weather_forecast",
                {"invalid_param": "test"}
            )
        except Exception as e:
            print(f"✓ Caught expected error for invalid params: {e}")
        
        # Test with missing required parameters
        try:
            # This will fail at Pydantic model creation
            invalid_request = ForecastRequest(days=3)  # Missing required 'location'
        except Exception as e:
            print(f"✓ Caught expected error for missing location: {e}")
        
        # Test calling non-existent tool
        try:
            result = await client.call_tool(
                "non_existent_tool",
                {}
            )
        except Exception as e:
            print(f"✓ Caught expected error for non-existent tool: {e}")


async def main():
    """Main entry point - demonstrates proper async patterns."""
    print("FastMCP Forecast Server - Client Demo")
    print("=" * 50)
    print("This demo uses proper async-only patterns throughout.")
    
    try:
        # Test basic HTTP connection
        await test_forecast_server_http()
        
        # Test with callbacks
        await test_with_callbacks()
        
        # Test error handling
        await test_error_handling()
        
        print("\n\n✅ All tests completed successfully!")
        print("Note: This client uses pure async patterns - no sync/async mixing!")
        
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        raise


if __name__ == "__main__":
    # This is the ONLY place where asyncio.run() should be used
    # It's the entry point that bootstraps the async code
    asyncio.run(main())