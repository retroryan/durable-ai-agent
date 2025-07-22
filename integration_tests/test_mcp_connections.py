#!/usr/bin/env python3
"""Test MCP server connections via HTTP (and optionally STDIO).

By default, tests all three HTTP MCP servers (forecast, historical, agricultural).
Use --stdio flag to also test STDIO connection.

Usage:
    poetry run python integration_tests/test_mcp_connections.py          # Test all HTTP servers
    poetry run python integration_tests/test_mcp_connections.py --stdio  # Test HTTP + STDIO
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


async def test_stdio_connection():
    """Test STDIO connection to forecast server."""
    print("\n=== Testing STDIO Connection ===")
    
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
        # Test connection
        print("1. Connecting to STDIO server...")
        client = await manager.get_client(stdio_server_def)
        print("✓ Connected to STDIO server")
        
        # List tools
        print("2. Listing tools...")
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools")
        for tool in tools:
            print(f"   - {tool.name}")
        
        # Test a simple tool call
        print("3. Testing tool invocation...")
        result = await client.call_tool(
            "get_weather_forecast", 
            {"request": {"location": "Seattle", "days": 1}}
        )
        
        # Handle result format
        if isinstance(result, list):
            data = json.loads(result[0].text)
        else:
            data = json.loads(result.content[0].text)
        
        print(f"✓ Got weather for {data['location_info']['name']}")
        
        # Cleanup
        await manager.cleanup()
        print("✓ STDIO connection test passed!")
        return True
        
    except Exception as e:
        print(f"✗ STDIO Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        await manager.cleanup()
        return False


async def test_http_server(server_name, server_def, test_params):
    """Test HTTP connection to a specific MCP server."""
    print(f"\n=== Testing {server_name} Server (HTTP) ===")
    print(f"URL: {server_def['url']}")
    
    manager = MCPClientManager()
    
    try:
        # Test connection
        print("1. Connecting to server...")
        client = await manager.get_client(server_def)
        print("✓ Connected to server")
        
        # List tools
        print("2. Listing tools...")
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools")
        for tool in tools:
            print(f"   - {tool.name}")
        
        # Test a tool call with server-specific parameters
        if tools:
            tool_name = tools[0].name
            print(f"3. Testing tool invocation: {tool_name}")
            
            result = await client.call_tool(tool_name, {"request": test_params})
            
            # Handle result format
            if isinstance(result, list):
                result_text = result[0].text
            else:
                result_text = result.content[0].text
                
            # Verify we got JSON response
            data = json.loads(result_text)
            print(f"✓ Tool invocation successful, got response with {len(data)} keys")
        
        # Cleanup
        await manager.cleanup()
        print(f"✓ {server_name} server test passed!")
        return True
        
    except Exception as e:
        print(f"✗ {server_name} Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        await manager.cleanup()
        return False


async def test_all_http_servers():
    """Test all three HTTP MCP servers."""
    # Server configurations
    servers = [
        {
            "name": "Forecast",
            "def": {
                "name": "forecast-server-http",
                "connection_type": "http",
                "url": os.getenv("MCP_FORECAST_SERVER_URL", "http://localhost:7778/mcp"),
                "env": None,
            },
            "test_params": {"location": "Seattle", "days": 2}
        },
        {
            "name": "Historical",
            "def": {
                "name": "historical-server-http",
                "connection_type": "http",
                "url": os.getenv("MCP_HISTORICAL_SERVER_URL", "http://localhost:7779/mcp"),
                "env": None,
            },
            "test_params": {
                "location": "Chicago",
                "start_date": "2024-01-01",
                "end_date": "2024-01-07"
            }
        },
        {
            "name": "Agricultural",
            "def": {
                "name": "agricultural-server-http",
                "connection_type": "http",
                "url": os.getenv("MCP_AGRICULTURAL_SERVER_URL", "http://localhost:7780/mcp"),
                "env": None,
            },
            "test_params": {
                "location": "Iowa City",
                "crop_type": "corn",
                "days": 3
            }
        }
    ]
    
    passed = 0
    failed = 0
    
    for server in servers:
        if await test_http_server(server["name"], server["def"], server["test_params"]):
            passed += 1
        else:
            failed += 1
    
    return passed, failed


async def main():
    """Run connection tests based on command line arguments."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test MCP server connections")
    parser.add_argument(
        "--stdio", 
        action="store_true", 
        help="Also test STDIO connection (in addition to HTTP servers)"
    )
    args = parser.parse_args()
    
    print("MCP Connection Tests")
    print("===================")
    if args.stdio:
        print("Testing MCP servers via HTTP and STDIO")
    else:
        print("Testing MCP servers via HTTP only")
    print("")
    
    # Track overall results
    total_passed = 0
    total_failed = 0
    
    # Always test HTTP servers
    print("Note: Make sure all MCP servers are running:")
    print("  poetry run python scripts/run_mcp_servers.py")
    print("")
    
    http_passed, http_failed = await test_all_http_servers()
    total_passed += http_passed
    total_failed += http_failed
    
    # Test STDIO if requested
    if args.stdio:
        print("\n" + "=" * 50)
        print("STDIO Connection Test")
        print("=" * 50)
        if await test_stdio_connection():
            total_passed += 1
        else:
            total_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tests run: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n✓ All MCP connection tests passed!")
        return 0
    else:
        print(f"\n✗ {total_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)