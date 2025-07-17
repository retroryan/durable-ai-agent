#!/usr/bin/env python3
"""Docker Compose Proxy Integration Test.

This is a direct Python program (not pytest) to avoid complexity and issues
with async test runners and connection pooling.

Tests the weather proxy running in docker-compose on port 8001.

IMPORTANT: This test specifically validates PROXY MODE behavior where FastMCP's
mount() feature automatically prefixes tool names with the service name.
For example: "get_weather_forecast" becomes "forecast_get_weather_forecast"

This is the expected behavior when MCP_USE_PROXY=true (default).
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


async def test_proxy_integration():
    """Test docker-compose proxy integration."""
    print("=== Docker Compose Proxy Integration Test ===")

    # Use fixed URL for docker-compose proxy
    proxy_url = "http://localhost:8001/mcp"
    print(f"Using proxy URL: {proxy_url}")

    # Create manager
    manager = MCPClientManager()

    # HTTP server definition for proxy
    proxy_server_def = {
        "name": "weather-proxy-http",
        "connection_type": "http",
        "url": proxy_url,
        "env": None,
    }

    try:
        # Test 1: Get client connection
        print("\n1. Testing proxy connection...")
        client = await manager.get_client(proxy_server_def)
        print("✓ Connected to weather proxy")

        # Test 2: List tools from all services
        print("\n2. Testing unified tool listing...")
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools from unified proxy")

        # Check for tools from each service
        tool_names = [tool.name for tool in tools]

        # Forecast tools
        forecast_tools = [name for name in tool_names if name.startswith("forecast_")]
        print(f"  - Forecast tools: {len(forecast_tools)}")

        # Agricultural tools
        agricultural_tools = [
            name for name in tool_names if name.startswith("agricultural_")
        ]
        print(f"  - Agricultural tools: {len(agricultural_tools)}")

        # Historical tools
        historical_tools = [
            name for name in tool_names if name.startswith("historical_")
        ]
        print(f"  - Historical tools: {len(historical_tools)}")

        # Verify we have tools from all services
        assert len(forecast_tools) > 0, "No forecast tools found"
        assert len(agricultural_tools) > 0, "No agricultural tools found"
        assert len(historical_tools) > 0, "No historical tools found"
        print("✓ All service tools are available")

        # Test 3: Call forecast weather tool
        print("\n3. Testing forecast weather tool...")
        result = await client.call_tool(
            "forecast_get_weather_forecast", {"request": {"location": "Melbourne", "days": 2}}
        )

        # The proxy services return structured data
        print(f"✓ Forecast weather result: {type(result)}")

        # Test 4: Call agricultural tool
        print("\n4. Testing agricultural tool...")
        result = await client.call_tool(
            "agricultural_get_agricultural_conditions", {"request": {"location": "Sydney", "days": 3, "crop_type": "corn"}}
        )
        print(f"✓ Agricultural result: {type(result)}")

        # Test 5: Call historical tool
        print("\n5. Testing historical tool...")
        result = await client.call_tool(
            "historical_get_historical_weather",
            {"request": {"location": "Brisbane", "start_date": "2024-01-01", "end_date": "2024-01-07"}},
        )
        print(f"✓ Historical result: {type(result)}")

        # Test 6: Connection reuse
        print("\n6. Testing connection reuse...")
        client2 = await manager.get_client(proxy_server_def)
        assert client == client2
        print("✓ Connection properly reused")

        # Test 7: Multiple tool calls in sequence
        print("\n7. Testing multiple sequential calls...")
        for i in range(3):
            result = await client.call_tool(
                "forecast_get_weather_forecast", {"request": {"location": f"City{i}", "days": 1}}
            )
            print(f"  Call {i+1}: {type(result)}")
        print("✓ Multiple calls successful")

        # Cleanup
        await manager.cleanup()
        print("\n✓ All proxy integration tests passed!")
        return 0

    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        try:
            await manager.cleanup()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    print("Docker Compose Proxy Integration Test")
    print("=====================================")
    print("Make sure the weather proxy is running with:")
    print("  docker-compose --profile weather_proxy up -d weather-proxy")
    print("Or use: ./mcp_proxy/run_docker.sh")
    print("")

    exit_code = asyncio.run(test_proxy_integration())
    sys.exit(exit_code)
