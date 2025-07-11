#!/usr/bin/env python3
"""
Minimal FastMCP server to test Pydantic model parameters.
"""
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional

# Initialize server
server = FastMCP(name="test-server")


class TestRequest(BaseModel):
    """Simple test request model."""
    message: str = Field(..., description="Test message")
    count: int = Field(default=1, description="Repeat count")


@server.tool
async def echo_test(request: TestRequest) -> dict:
    """Simple echo tool that uses a Pydantic model."""
    return {
        "message": request.message,
        "count": request.count,
        "repeated": [request.message] * request.count
    }


@server.tool
async def simple_tool(text: str) -> str:
    """Simple tool with basic parameters."""
    return f"Echo: {text}"


if __name__ == "__main__":
    import os
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "7779"))
    print(f"Starting test server on {host}:{port}")
    server.run(transport="streamable-http", host=host, port=port, path="/mcp")