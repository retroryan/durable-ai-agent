#!/bin/bash
# Simple script to build and run the MCP proxy using docker-compose

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Starting MCP Proxy with docker-compose..."
cd "$PROJECT_ROOT"

# Start the weather proxy profile with rebuild
docker-compose --profile weather_proxy up -d --build weather-proxy

# Color codes
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Give it a moment to start
sleep 2

# Display success message
echo -e "${GREEN}✅ Services are running!${NC}"
echo ""
echo "📍 Available endpoints:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📡 API Server:        http://localhost:8000"
echo "  📚 API Documentation: http://localhost:8000/docs"
echo "  🔄 Temporal UI:       http://localhost:8080"
echo "  🌦️  Weather Proxy:     http://localhost:8001/mcp"
echo "  🎨 Frontend:          http://localhost:3000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Run ./test_docker.sh to test the proxy"
echo "Run ./stop_docker.sh to stop and remove the container"