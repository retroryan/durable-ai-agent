#!/bin/bash
# Rebuild and restart the worker

# Color codes
GREEN='\033[0;32m'
NC='\033[0m' # No Color

docker-compose build worker
docker-compose up -d --no-deps worker

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
