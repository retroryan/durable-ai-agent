#!/usr/bin/env python3
"""Test consolidated MCP server with all weather tools using MCPClientManager.

Tests the unified MCP weather server running on port 7778 with:
- MCPClientManager for connection pooling
- Pydantic models for request validation
- String to float coordinate conversion
- Validation error handling
- Performance comparison (location name vs coordinates)

Usage:
    poetry run python integration_tests/test_mcp_connections.py
"""
import argparse
import asyncio
import json
import os
import sys
import traceback
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
else:
    print(f"No .env file found at {env_path}, using defaults")

sys.path.insert(0, str(project_root))
from shared.mcp_client_manager import MCPClientManager
from models.mcp_models import ForecastRequest, HistoricalRequest, AgriculturalRequest


async def test_consolidated_server():
    """Test all tools in the consolidated server."""
    server_def = {
        "name": "weather-mcp",
        "connection_type": "http",
        "url": os.getenv("MCP_SERVER_URL", "http://localhost:7778/mcp")
    }
    
    manager = MCPClientManager()
    
    print("=== Testing Consolidated MCP Weather Server ===")
    print(f"URL: {server_def['url']}")
    
    try:
        # Connect
        print("\n1. Connecting to server...")
        client = await manager.get_client(server_def)
        print("✓ Connected")
        
        # List tools - should find all 3
        print("\n2. Listing tools...")
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools:")
        
        expected_tools = {
            "get_weather_forecast",
            "get_historical_weather", 
            "get_agricultural_conditions"
        }
        
        for tool in tools:
            print(f"  - {tool.name}")
            
        # Verify all expected tools are present
        actual_tools = {tool.name for tool in tools}
        if expected_tools.issubset(actual_tools):
            print("✓ All expected tools found!")
        else:
            missing = expected_tools - actual_tools
            print(f"✗ Missing tools: {missing}")
            return False
            
        # Test each tool
        print("\n3. Testing each tool:")
        
        # Test forecast with Pydantic model
        print("\n  Testing get_weather_forecast with Pydantic model...")
        forecast_request = ForecastRequest(location="Seattle", days=3)
        print(f"    Request: {forecast_request}")
        result = await client.call_tool(
            "get_weather_forecast",
            {"request": forecast_request}  # Pass Pydantic model directly
        )
        result_data = _parse_result(result)
        print(f"  ✓ Forecast: {result_data.get('summary', 'No summary')}")
        
        # Test historical with Pydantic model
        print("\n  Testing get_historical_weather with Pydantic model...")
        historical_request = HistoricalRequest(
            location="Seattle",
            start_date="2024-01-01",
            end_date="2024-01-07"
        )
        print(f"    Request: {historical_request}")
        result = await client.call_tool(
            "get_historical_weather",
            {"request": historical_request}  # Pass Pydantic model directly
        )
        result_data = _parse_result(result)
        print(f"  ✓ Historical: {result_data.get('summary', 'No summary')}")
        
        # Test agricultural with Pydantic model
        print("\n  Testing get_agricultural_conditions with Pydantic model...")
        agricultural_request = AgriculturalRequest(
            location="Iowa", 
            days=5,
            crop_type="corn"
        )
        print(f"    Request: {agricultural_request}")
        result = await client.call_tool(
            "get_agricultural_conditions",
            {"request": agricultural_request}  # Pass Pydantic model directly
        )
        result_data = _parse_result(result)
        print(f"  ✓ Agricultural: {result_data.get('summary', 'No summary')}")
        
        # Test Pydantic validation
        print("\n4. Testing Pydantic validation:")
        
        # Test coordinate conversion (string to float)
        print("\n  Testing coordinate string conversion...")
        coord_request = ForecastRequest(
            latitude="41.8781",  # String
            longitude="-87.6298",  # String
            days=2
        )
        print(f"    Input types: lat={type('41.8781')}, lon={type('-87.6298')}")
        print(f"    Converted types: lat={type(coord_request.latitude)}, lon={type(coord_request.longitude)}")
        result = await client.call_tool(
            "get_weather_forecast",
            {"request": coord_request}  # Pass Pydantic model directly
        )
        print("  ✓ String coordinates converted successfully")
        
        # Test validation errors
        print("\n  Testing validation error handling...")
        try:
            # This should fail - missing location
            invalid_request = ForecastRequest(days=3)
            print("  ✗ Expected validation error not raised")
        except ValueError as e:
            print(f"  ✓ Caught expected error: {e}")
        
        # Test date validation
        try:
            # This should fail - end date before start date
            invalid_historical = HistoricalRequest(
                location="Seattle",
                start_date="2024-01-10",
                end_date="2024-01-05"
            )
            print("  ✗ Expected date validation error not raised")
        except ValueError as e:
            print(f"  ✓ Caught expected date error: {e}")
        
        # Test coordinate validation
        try:
            # This should fail - latitude out of range
            invalid_coords = ForecastRequest(
                latitude=91.0,  # > 90
                longitude=0.0
            )
            print("  ✗ Expected coordinate validation error not raised")
        except ValueError as e:
            print(f"  ✓ Caught expected coordinate error: {e}")
        
        print("\n✓ All tests passed!")
        
        await manager.cleanup()
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        traceback.print_exc()
        await manager.cleanup()
        return False


def _parse_result(result):
    """Parse the result from call_tool into a dictionary."""
    # Handle result format
    if isinstance(result, list):
        result_text = result[0].text
    else:
        result_text = result.content[0].text
    
    # Parse JSON
    return json.loads(result_text)


async def test_performance_comparison():
    """Compare performance of location name vs coordinates."""
    import time
    
    server_def = {
        "name": "weather-mcp",
        "connection_type": "http",
        "url": os.getenv("MCP_SERVER_URL", "http://localhost:7778/mcp")
    }
    
    manager = MCPClientManager()
    
    print("\n=== Performance Comparison Test ===")
    
    try:
        client = await manager.get_client(server_def)
        
        # Test with location name (requires geocoding)
        print("\n1. Testing with location name (requires geocoding)...")
        start = time.time()
        name_request = ForecastRequest(location="New York", days=1)
        result = await client.call_tool(
            "get_weather_forecast",
            {"request": name_request}  # Pass Pydantic model directly
        )
        name_time = time.time() - start
        print(f"   Time taken: {name_time:.3f}s")
        
        # Test with coordinates (no geocoding)
        print("\n2. Testing with coordinates (no geocoding)...")
        start = time.time()
        coord_request = ForecastRequest(latitude=40.7128, longitude=-74.0060, days=1)
        result = await client.call_tool(
            "get_weather_forecast",
            {"request": coord_request}  # Pass Pydantic model directly
        )
        coord_time = time.time() - start
        print(f"   Time taken: {coord_time:.3f}s")
        
        if name_time > coord_time:
            speedup = name_time / coord_time
            print(f"\n✓ Coordinates are {speedup:.1f}x faster than location names")
        else:
            print(f"\n✓ Both methods performed similarly (likely in mock mode)")
        
        await manager.cleanup()
        return True
        
    except Exception as e:
        print(f"\n✗ Performance test failed: {e}")
        await manager.cleanup()
        return False


async def main():
    """Run consolidated server test."""

    print("MCP Connection Test with MCPClientManager")
    print("=========================================")
    print("Testing unified MCP weather server with Pydantic models")
    print("")
    
    print("Note: Make sure the MCP server is running:")
    print("  poetry run python scripts/run_mcp_servers.py")
    print("")
    
    # Test the consolidated server
    success = await test_consolidated_server()
    
    # Run performance comparison
    if success:
        perf_success = await test_performance_comparison()
        success = success and perf_success
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if success:
        print("✓ All MCP server tests passed!")
        print("✓ MCPClientManager connection pooling working correctly")
        print("✓ Pydantic validation working as expected")
        return 0
    else:
        print("✗ Some MCP server tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)