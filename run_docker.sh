#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
RUN_CLIENT=false
REFRESH_FRONT=false
REFRESH_WORKER=false
for arg in "$@"; do
    case $arg in
        --run_client)
            RUN_CLIENT=true
            shift
            ;;
        --front)
            REFRESH_FRONT=true
            shift
            ;;
        --worker)
            REFRESH_WORKER=true
            shift
            ;;
    esac
done

# Handle refresh operations
if [ "$REFRESH_FRONT" = true ]; then
    echo -e "${BLUE}🔄 Refreshing API server...${NC}"
    docker-compose build api
    docker-compose up -d --no-deps api
    echo -e "${GREEN}✅ API server refreshed${NC}"
    exit 0
fi

if [ "$REFRESH_WORKER" = true ]; then
    echo -e "${BLUE}🔄 Refreshing worker...${NC}"
    docker-compose build worker
    docker-compose up -d --no-deps worker
    echo -e "${GREEN}✅ Worker refreshed${NC}"
    
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
    exit 0
fi

# Ensure logs directory exists
mkdir -p logs

# Ensure mcp_servers directory is available
echo -e "${BLUE}📦 Preparing mcp_servers directory...${NC}"
if [ -d "mcp_servers" ]; then
    echo -e "${GREEN}✓ mcp_servers directory found${NC}"
else
    echo -e "${YELLOW}⚠️  mcp_servers directory not found${NC}"
fi

echo -e "${BLUE}🔨 Rebuilding Docker containers...${NC}"
docker-compose build

# Determine which profiles to use
if [ "$RUN_CLIENT" = true ]; then
    echo -e "\n${BLUE}🚀 Starting services with docker-compose (including API server, frontend, and weather proxy)...${NC}"
    docker-compose --profile weather_proxy --profile api_server up -d
else
    echo -e "\n${BLUE}🚀 Starting services with docker-compose (weather proxy only, no API server or frontend)...${NC}"
    docker-compose --profile weather_proxy up -d
fi

# Wait for services to be ready
echo -e "\n${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "\n${GREEN}✅ Services are running!${NC}"
    echo -e "\n${GREEN}📍 Available endpoints:${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ "$RUN_CLIENT" = true ]; then
        echo -e "  📡 API Server:        http://localhost:8000"
        echo -e "  📚 API Documentation: http://localhost:8000/docs"
    fi
    echo -e "  🔄 Temporal UI:       http://localhost:8080"
    echo -e "  🌦️  Weather Proxy:     http://localhost:8001/mcp"
    if [ "$RUN_CLIENT" = true ]; then
        echo -e "  🎨 Frontend:          http://localhost:3000"
    fi
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\n${BLUE}💡 View logs with: docker-compose logs -f${NC}"
    echo -e "${BLUE}📁 Application logs are written to: ./logs/${NC}"
    
    if [ "$RUN_CLIENT" = false ]; then
        echo -e "\n${YELLOW}📌 Note: API server was not started (--run_client flag not provided)${NC}"
        echo -e "${YELLOW}   You can now run the API server locally using:${NC}"
        echo -e "${GREEN}   ./scripts/run_api_local.sh${NC}"
    fi
else
    echo -e "\n${YELLOW}⚠️  Some services may still be starting up...${NC}"
    echo -e "Check status with: docker-compose ps"
fi