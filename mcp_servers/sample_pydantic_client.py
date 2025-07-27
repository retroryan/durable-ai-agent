#!/usr/bin/env python3
"""
Sample client demonstrating proper Pydantic model usage with FastMCP.

This shows how to:
1. Import shared Pydantic models
2. Create model instances with validation
3. Call MCP tools with Pydantic models
4. Handle validation errors
"""

import asyncio
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import Client
from models.mcp_models import ForecastRequest, HistoricalRequest, AgriculturalRequest


async def demonstrate_pydantic_usage():
    """Demonstrate proper Pydantic usage patterns with FastMCP."""
    
    # Connect to the consolidated agricultural server
    client = Client("http://localhost:7778/mcp")
    
    async with client:
        print("=== Pydantic Model Usage Demo ===\n")
        
        # 1. Basic usage with location name
        print("1. Basic forecast with location name:")
        request1 = ForecastRequest(location="San Francisco", days=3)
        print(f"   Created: {request1}")
        result = await client.call_tool("get_weather_forecast", {"request": request1})
        # Handle CallToolResult properly
        if hasattr(result, 'content') and result.content:
            print(f"   Result: {result.content[0].text[:100]}...\n")
        else:
            print(f"   Result: {str(result)[:100]}...\n")
        
        # 2. Using coordinates (faster than geocoding)
        print("2. Forecast with coordinates (faster):")
        request2 = ForecastRequest(
            latitude=40.7128,
            longitude=-74.0060,
            days=5
        )
        print(f"   Created: {request2}")
        result = await client.call_tool("get_weather_forecast", {"request": request2})
        if hasattr(result, 'content') and result.content:
            print(f"   Result: {result.content[0].text[:100]}...\n")
        else:
            print(f"   Result: {str(result)[:100]}...\n")
        
        # 3. Validation error handling
        print("3. Validation error handling:")
        try:
            # This will fail - missing location
            invalid_request = ForecastRequest(days=3)
        except ValueError as e:
            print(f"   ✓ Caught expected error: {e}\n")
        
        # 4. String coordinate conversion (AWS Bedrock compatibility)
        print("4. String coordinate conversion:")
        request4 = ForecastRequest(
            latitude="41.8781",  # String will be converted to float
            longitude="-87.6298",  # String will be converted to float
            days=1
        )
        print(f"   Created: {request4}")
        print(f"   Latitude type: {type(request4.latitude)} = {request4.latitude}")
        print(f"   Longitude type: {type(request4.longitude)} = {request4.longitude}\n")
        
        # 5. Historical weather with date validation
        print("5. Historical weather with date validation:")
        request5 = HistoricalRequest(
            location="London",
            start_date="2025-01-01",
            end_date="2025-01-07"
        )
        print(f"   Created: {request5}")
        result = await client.call_tool("get_historical_weather", {"request": request5})
        if hasattr(result, 'content') and result.content:
            print(f"   Result: {result.content[0].text[:100]}...\n")
        else:
            print(f"   Result: {str(result)[:100]}...\n")
        
        # 6. Agricultural conditions with crop type
        print("6. Agricultural conditions with crop type:")
        request6 = AgriculturalRequest(
            location="Iowa",
            days=7,
            crop_type="corn"
        )
        print(f"   Created: {request6}")
        result = await client.call_tool("get_agricultural_conditions", {"request": request6})
        if hasattr(result, 'content') and result.content:
            print(f"   Result: {result.content[0].text[:100]}...\n")
        else:
            print(f"   Result: {str(result)[:100]}...\n")
        
        # 7. Edge case testing
        print("7. Edge case testing:")
        
        # Maximum days
        edge1 = ForecastRequest(location="Tokyo", days=16)
        print(f"   Max days (16): {edge1.days}")
        
        # Days beyond max (will be clamped by Pydantic)
        try:
            edge2 = ForecastRequest(location="Paris", days=20)
        except ValueError as e:
            print(f"   Days > 16 validation: {e}")
        
        # Latitude validation
        try:
            edge3 = ForecastRequest(latitude=91, longitude=0)
        except ValueError as e:
            print(f"   Invalid latitude: {e}")
        
        # Date order validation
        try:
            edge4 = HistoricalRequest(
                location="Berlin",
                start_date="2025-01-10",
                end_date="2025-01-05"  # End before start
            )
        except ValueError as e:
            print(f"   Date order validation: {e}\n")
        
        print("=== Demo Complete ===")


async def performance_comparison():
    """Compare performance of location name vs coordinates."""
    client = Client("http://localhost:7778/mcp")
    
    async with client:
        print("\n=== Performance Comparison ===\n")
        
        # Location name (requires geocoding)
        import time
        start = time.time()
        request1 = ForecastRequest(location="New York", days=1)
        result1 = await client.call_tool("get_weather_forecast", {"request": request1})
        time1 = time.time() - start
        print(f"Location name lookup: {time1:.2f}s")
        
        # Coordinates (no geocoding needed)
        start = time.time()
        request2 = ForecastRequest(latitude=40.7128, longitude=-74.0060, days=1)
        result2 = await client.call_tool("get_weather_forecast", {"request": request2})
        time2 = time.time() - start
        print(f"Direct coordinates: {time2:.2f}s")
        
        print(f"Speedup: {time1/time2:.1f}x faster with coordinates\n")


if __name__ == "__main__":
    print("Starting Pydantic MCP Client Demo...")
    print("Make sure the MCP server is running on port 7778\n")
    
    try:
        asyncio.run(demonstrate_pydantic_usage())
        asyncio.run(performance_comparison())
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the MCP server is running with:")
        print("  poetry run python mcp_servers/agricultural_server.py")