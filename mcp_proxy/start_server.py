#!/usr/bin/env python3
"""Simple script to start the MCP proxy server."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

from mcp_proxy.main import app

if __name__ == "__main__":
    port = int(os.getenv("MCP_PROXY_PORT", 8000))
    print(f"Starting MCP Proxy Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
