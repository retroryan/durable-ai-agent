#!/bin/bash

# Test script for the MCP forecast server sample client

echo "Testing MCP Forecast Server Client"
echo "=================================="
echo ""

# Check if fastmcp is installed
if ! python -c "import fastmcp" 2>/dev/null; then
    echo "Error: fastmcp is not installed!"
    echo "Please install it with: pip install fastmcp"
    exit 1
fi

# Run from the project root directory
cd "$(dirname "$0")/.." || exit 1

# Check if the server is running
echo "Checking if forecast server is running on port 7778..."
if ! curl -s http://127.0.0.1:7778/health >/dev/null 2>&1; then
    echo "Error: Forecast server is not running!"
    echo ""
    echo "Please start the server first in a separate terminal:"
    echo "  ./mcp_servers/start_mcp_servers.sh"
    echo ""
    echo "Or run directly:"
    echo "  python mcp_servers/forecast_server.py"
    exit 1
fi

echo "✓ Server is running"
echo ""

# Run the sample client
echo "Running sample client..."
echo ""

python mcp_servers/sample_client.py

echo ""
echo "Test completed!"