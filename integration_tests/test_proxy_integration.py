#!/usr/bin/env python3
"""Docker Compose Proxy Integration Test.

This is a direct Python program (not pytest) to avoid complexity and issues
with async test runners and connection pooling.

Tests the weather proxy running in docker-compose on port 8001.
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

        # Current tools
        current_tools = [name for name in tool_names if name.startswith("current_")]
        print(f"  - Current tools: {len(current_tools)}")

        # Historical tools
        historical_tools = [
            name for name in tool_names if name.startswith("historical_")
        ]
        print(f"  - Historical tools: {len(historical_tools)}")

        # Verify we have tools from all services
        assert len(forecast_tools) > 0, "No forecast tools found"
        assert len(current_tools) > 0, "No current tools found"
        assert len(historical_tools) > 0, "No historical tools found"
        print("✓ All service tools are available")

        # Test 3: Call current weather tool
        print("\n3. Testing current weather tool...")
        result = await client.call_tool(
            "current_get_current_weather", {"location": "Melbourne"}
        )

        # The proxy services return simple strings for demo
        print(f"✓ Current weather result: {result}")

        # Test 4: Call forecast tool
        print("\n4. Testing forecast tool...")
        result = await client.call_tool(
            "forecast_get_forecast", {"location": "Sydney", "days": 3}
        )
        print(f"✓ Forecast result: {result}")

        # Test 5: Call historical tool
        print("\n5. Testing historical tool...")
        result = await client.call_tool(
            "historical_get_historical_weather",
            {"location": "Brisbane", "date": "2024-01-01"},
        )
        print(f"✓ Historical result: {result}")

        # Test 6: Connection reuse
        print("\n6. Testing connection reuse...")
        client2 = await manager.get_client(proxy_server_def)
        assert client == client2
        print("✓ Connection properly reused")

        # Test 7: Multiple tool calls in sequence
        print("\n7. Testing multiple sequential calls...")
        for i in range(3):
            result = await client.call_tool(
                "current_get_temperature", {"location": f"City{i}"}
            )
            print(f"  Call {i+1}: {result}")
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
