#!/usr/bin/env python3
"""Simple HTTP client integration test.

This is a direct Python program (not pytest) to avoid complexity and issues
with async test runners and connection pooling.
"""
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


async def test_http_client():
    """Test HTTP client connection and basic operations."""
    print("=== HTTP Client Integration Test ===")

    # Get MCP server configuration from environment
    mcp_host = os.getenv("MCP_FORECAST_SERVER_HOST", "localhost")
    mcp_port = os.getenv("MCP_FORECAST_SERVER_PORT", "7778")
    mcp_url = os.getenv("MCP_FORECAST_SERVER_URL", f"http://{mcp_host}:{mcp_port}/mcp")

    print(f"Using MCP server URL: {mcp_url}")

    # Create manager
    manager = MCPClientManager()

    # HTTP server definition
    http_server_def = {
        "name": "forecast-server-http",
        "connection_type": "http",
        "url": mcp_url,
        "env": None,
    }

    try:
        # Test 1: Get client connection
        print("\n1. Testing client connection...")
        client = await manager.get_client(http_server_def)
        print("✓ Connected to HTTP server")

        # Test 2: List tools
        print("\n2. Testing tool listing...")
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools")
        assert any(tool.name == "get_weather_forecast" for tool in tools)
        print("✓ Found get_weather_forecast tool")

        # Test 3: Tool invocation with location
        print("\n3. Testing tool invocation with location...")
        result = await client.call_tool(
            "get_weather_forecast", {"request": {"location": "New York", "days": 3}}
        )

        # Handle result format (list of TextContent objects)
        if isinstance(result, list):
            data = json.loads(result[0].text)
        else:
            data = json.loads(result.content[0].text)

        assert data["location_info"]["name"] == "New York"
        assert "temperature_2m" in data["current"]
        print(f"✓ Got weather for {data['location_info']['name']}")
        print(f"  Current temp: {data['current']['temperature_2m']}°C")

        # Test 4: Tool invocation with coordinates
        print("\n4. Testing tool invocation with coordinates...")
        result = await client.call_tool(
            "get_weather_forecast",
            {"request": {"latitude": 51.5074, "longitude": -0.1278, "days": 3}},
        )

        # Handle result format
        if isinstance(result, list):
            data = json.loads(result[0].text)
        else:
            data = json.loads(result.content[0].text)

        assert data["location_info"]["coordinates"]["latitude"] == 51.5074
        assert data["location_info"]["coordinates"]["longitude"] == -0.1278
        print("✓ Got weather for coordinates")
        print(f"  Lat: {data['location_info']['coordinates']['latitude']}")
        print(f"  Lon: {data['location_info']['coordinates']['longitude']}")

        # Test 5: Connection reuse
        print("\n5. Testing connection reuse...")
        client2 = await manager.get_client(http_server_def)
        assert client == client2
        print("✓ Connection properly reused")

        # Cleanup
        await manager.cleanup()
        print("\n✓ All tests passed!")
        return 0

    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_http_client())
    sys.exit(exit_code)
