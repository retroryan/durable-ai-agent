#!/usr/bin/env python3
"""Test script to reproduce MCP freezing issue with httpx deprecation warning."""

import asyncio
import logging
import os
from fastmcp import Client
from models.tool_definitions import MCPServerDefinition

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_mcp_client():
    """Test MCP client connection and tool call."""
    # Create HTTP transport configuration
    server_def = MCPServerDefinition(
        name="test-weather-proxy",
        connection_type="http",
        url=os.getenv("MCP_URL", "http://localhost:8001/mcp")
    )
    
    logger.info(f"Creating client with URL: {server_def.url}")
    
    # Create client
    client = Client(server_def.url)
    
    try:
        # Use async context manager properly
        async with client:
            logger.info("Client connected successfully")
            
            # Try to call a tool
            tool_args = {"request": {"location": "San Francisco, CA"}}
            logger.info("Calling forecast_get_weather_forecast tool...")
            
            result = await client.call_tool(
                name="forecast_get_weather_forecast",
                arguments=tool_args
            )
            
            logger.info(f"Tool result: {result}")
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    
    logger.info("Test completed")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_mcp_client())