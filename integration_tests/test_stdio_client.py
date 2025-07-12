#!/usr/bin/env python3
"""Simple stdio client integration test.

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
from shared.mcp_client_manager_v2 import MCPClientManager


async def test_stdio_client():
    """Test stdio client connection and basic operations."""
    print("=== Stdio Client Integration Test ===")

    # Create manager
    manager = MCPClientManager()

    # Stdio server definition - path relative to project root
    forecast_server_path = project_root / "mcp_servers" / "forecast_server.py"

    stdio_server_def = {
        "name": "forecast-server-stdio",
        "connection_type": "stdio",
        "command": "python",
        "args": [str(forecast_server_path), "--transport", "stdio"],
        "env": None,
    }

    print(f"Using forecast server at: {forecast_server_path}")

    try:
        # Test 1: Get client connection
        print("\n1. Testing client connection...")
        client = await manager.get_client(stdio_server_def)
        print("✓ Connected to stdio server")

        # Test 2: List tools
        print("\n2. Testing tool listing...")
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools")
        assert any(tool.name == "get_weather_forecast" for tool in tools)
        print("✓ Found get_weather_forecast tool")

        # Test 3: Tool invocation with location
        print("\n3. Testing tool invocation with location...")
        result = await client.call_tool(
            "get_weather_forecast", {"request": {"location": "Paris", "days": 3}}
        )

        # Handle result format (list of TextContent objects)
        if isinstance(result, list):
            data = json.loads(result[0].text)
        else:
            data = json.loads(result.content[0].text)

        assert data["location_info"]["name"] == "Paris"
        assert "temperature_2m" in data["current"]
        print(f"✓ Got weather for {data['location_info']['name']}")
        print(f"  Current temp: {data['current']['temperature_2m']}°C")

        # Test 4: Multiple invocations
        print("\n4. Testing multiple invocations...")
        locations = ["London", "Tokyo", "Sydney"]
        for location in locations:
            result = await client.call_tool(
                "get_weather_forecast", {"request": {"location": location, "days": 2}}
            )

            # Handle result format
            if isinstance(result, list):
                data = json.loads(result[0].text)
            else:
                data = json.loads(result.content[0].text)

            assert data["location_info"]["name"] == location
            print(f"✓ Got weather for {location}")

        # Test 5: Connection reuse
        print("\n5. Testing connection reuse...")
        client2 = await manager.get_client(stdio_server_def)
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
    exit_code = asyncio.run(test_stdio_client())
    sys.exit(exit_code)
