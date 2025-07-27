#!/usr/bin/env python3
"""Debug MCP tool execution to understand validation error."""
import asyncio
import logging
from shared.mcp_client_manager import MCPClientManager
from models.tool_definitions import MCPServerDefinition

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_mcp_call():
    """Test direct MCP call with the failing arguments."""
    manager = MCPClientManager()
    
    # Create server definition for proxy
    server_def = MCPServerDefinition(
        name="weather_proxy",
        url="http://localhost:8001/mcp"
    )
    
    # Get client
    client = await manager.get_client(server_def)
    
    # Test arguments that are failing
    args = {
        "days": 7,
        "latitude": "47.6062",
        "longitude": "-122.3321"
    }
    
    print(f"Testing with args: {args}")
    print(f"Arg types: days={type(args['days'])}, lat={type(args['latitude'])}, lon={type(args['longitude'])}")
    
    try:
        # Call the tool
        result = await client.call_tool(
            name="forecast_get_weather_forecast",
            arguments=args
        )
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(test_mcp_call())