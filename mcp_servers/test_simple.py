#!/usr/bin/env python3
"""
Minimal test to debug the connection issue.
"""

import asyncio

from fastmcp import Client


async def test_connection():
    """Test basic connection to the server."""
    try:
        # Try without trailing slash
        print("Testing connection to http://127.0.0.1:7778/mcp")
        client = Client("http://127.0.0.1:7778/mcp")

        async with client:
            print("✓ Connected successfully!")

            # Try to list tools
            tools = await client.list_tools()
            print(f"✓ Found {len(tools)} tools")

            for tool in tools:
                print(f"  - {tool.name}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(test_connection())
