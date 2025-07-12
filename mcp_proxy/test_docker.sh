#!/bin/bash
# Simple script to test the MCP proxy running in Docker

echo "Testing MCP Proxy Docker container..."
echo ""

# Check if container is running
echo "1. Checking if container is running..."
if docker ps | grep -q durable-weather-proxy; then
    echo "✅ MCP Proxy container is running"
else
    echo "❌ MCP Proxy container is not running"
    echo "Make sure it's running with ./run_docker.sh"
    exit 1
fi

echo ""
echo "2. Running Python MCP client test..."
# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"
if [ -f "mcp_proxy/test_docker_proxy.py" ]; then
    echo "Connecting to proxy with MCP client..."
    python3 mcp_proxy/test_docker_proxy.py
    if [ $? -eq 0 ]; then
        echo "✅ MCP client test successful"
    else
        echo "❌ MCP client test failed"
        exit 1
    fi
else
    echo "⚠️  Python test script not found at mcp_proxy/test_docker_proxy.py"
    exit 1
fi

echo ""
echo "3. Testing manual curl (optional)..."
echo "You can test the proxy manually with:"
echo "curl -X POST http://localhost:8001/mcp -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/list\",\"id\":1}'"

echo ""
echo "✅ All tests completed!"