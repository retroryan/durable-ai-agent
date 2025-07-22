#!/usr/bin/env python3
"""Simple test to check MCP client lifecycle and httpx warnings."""

import asyncio
import logging
import warnings

# Capture warnings
warnings.filterwarnings('always', category=DeprecationWarning)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_fastmcp_client_lifecycle():
    """Test the FastMCP client lifecycle to see if it causes the httpx warning."""
    from fastmcp import Client
    
    # Test 1: Using context manager properly
    logger.info("Test 1: Using async context manager")
    try:
        client = Client("http://localhost:8001/mcp")
        async with client:
            logger.info("Client entered context")
            # Simulate some work
            await asyncio.sleep(0.1)
        logger.info("Client exited context properly")
    except Exception as e:
        logger.error(f"Error in test 1: {e}")
    
    # Test 2: Manual __aenter__ and __aexit__ (like MCPClientManager does)
    logger.info("\nTest 2: Manual __aenter__ and __aexit__")
    try:
        client = Client("http://localhost:8001/mcp")
        await client.__aenter__()
        logger.info("Client entered via __aenter__")
        # Simulate some work
        await asyncio.sleep(0.1)
        await client.__aexit__(None, None, None)
        logger.info("Client exited via __aexit__")
    except Exception as e:
        logger.error(f"Error in test 2: {e}")
    
    # Test 3: Not closing the client (to trigger warning)
    logger.info("\nTest 3: Creating client without closing")
    try:
        client = Client("http://localhost:8001/mcp")
        # Don't use context manager or close it
        logger.info("Client created but not closed")
    except Exception as e:
        logger.error(f"Error in test 3: {e}")
    
    # Give time for warnings to appear
    await asyncio.sleep(0.5)
    logger.info("Tests completed")

if __name__ == "__main__":
    asyncio.run(test_fastmcp_client_lifecycle())