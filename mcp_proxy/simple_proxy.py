"""
Simple MCP Proxy using FastMCP's built-in HTTP transport.

This demonstrates the CORRECT way to create an MCP proxy server.
"""

import os
import logging
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_unified_proxy():
    """Create a unified proxy that combines all weather services."""
    # Import the service modules
    from mcp_proxy.services import forecast_server, current_server, historical_server
    
    # Create the main proxy server
    proxy = FastMCP("UnifiedWeatherProxy")
    
    # Mount each service with a prefix
    proxy.mount("forecast", forecast_server.server)
    proxy.mount("current", current_server.server)
    proxy.mount("historical", historical_server.server)
    
    logger.info("Created unified proxy with all weather services")
    return proxy


if __name__ == "__main__":
    # Create the unified proxy
    proxy = create_unified_proxy()
    
    # Run with HTTP transport - FastMCP handles all the protocol details!
    port = int(os.getenv("MCP_PROXY_PORT", 8000))
    logger.info(f"Starting MCP Proxy Server on port {port}")
    
    # This is the CORRECT way - let FastMCP handle the HTTP transport
    proxy.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        path="/mcp"  # MCP endpoint will be at http://localhost:8000/mcp
    )