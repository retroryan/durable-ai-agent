#!/usr/bin/env python3
"""Test the simple MCP proxy using FastMCP client."""

import asyncio
from fastmcp.client import Client


async def test_proxy():
    """Test the proxy using MCP client."""
    # Connect to the proxy server
    proxy_url = "http://localhost:8001/mcp"
    
    print(f"Connecting to proxy at {proxy_url}...")
    
    async with Client(proxy_url) as client:
        print("✅ Connected to proxy!")
        
        # List all tools
        print("\nListing all tools...")
        tools = await client.list_tools()
        
        print(f"\nFound {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Test calling a tool
        print("\nTesting tool calls...")
        
        # Test current weather (no prefix needed - mounted as "current")
        result = await client.call_tool(
            "current_get_current_weather",
            {"location": "Melbourne"}
        )
        print(f"\nCurrent weather result: {result}")
        
        # Test forecast
        result = await client.call_tool(
            "forecast_get_forecast",
            {"location": "Sydney", "days": 3}
        )
        print(f"\nForecast result: {result}")
        
        # Test historical
        result = await client.call_tool(
            "historical_get_historical_weather",
            {"location": "Brisbane", "date": "2024-01-01"}
        )
        print(f"\nHistorical result: {result}")


if __name__ == "__main__":
    asyncio.run(test_proxy())