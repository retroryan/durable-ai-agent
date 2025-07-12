#!/bin/bash
# Simple script to stop and remove the MCP proxy Docker container

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Stopping MCP Proxy with docker-compose..."
cd "$PROJECT_ROOT"

# Stop the weather proxy profile
docker-compose --profile weather_proxy down

echo "✅ MCP Proxy container stopped and removed"