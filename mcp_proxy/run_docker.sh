#!/bin/bash
# Simple script to build and run the MCP proxy using docker-compose

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting MCP Proxy with docker-compose..."
cd "$PROJECT_ROOT"

# Start the weather proxy profile with rebuild
docker-compose --profile weather_proxy up -d --build weather-proxy

echo "✅ MCP Proxy is running at http://localhost:8001/mcp"
echo "Run ./test_docker.sh to test the proxy"
echo "Run ./stop_docker.sh to stop and remove the container"