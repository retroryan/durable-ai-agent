#!/bin/bash
# Simple script to build and run the MCP proxy Docker container

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Building MCP Proxy Docker image..."
docker build -f "$SCRIPT_DIR/Dockerfile" -t mcp-proxy "$SCRIPT_DIR/.."

echo "Starting MCP Proxy container..."
docker run -d --name mcp-proxy -p 8000:8000 mcp-proxy

echo "✅ MCP Proxy is running at http://localhost:8000/mcp"
echo "Run ./test_docker.sh to test the proxy"
echo "Run ./stop_docker.sh to stop and remove the container"