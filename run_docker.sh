#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

echo -e "\n${BLUE}🚀 Starting services with docker-compose (including weather proxy)...${NC}"
docker-compose --profile weather_proxy up -d

# Wait for services to be ready
echo -e "\n${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "\n${GREEN}✅ Services are running!${NC}"
    echo -e "\n${GREEN}📍 Available endpoints:${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  📡 API Server:        http://localhost:8000"
    echo -e "  📚 API Documentation: http://localhost:8000/docs"
    echo -e "  🔄 Temporal UI:       http://localhost:8080"
    echo -e "  🌦️  Weather Proxy:     http://localhost:8001/mcp"
    echo -e "  🎨 Frontend:          http://localhost:3000"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\n${BLUE}💡 View logs with: docker-compose logs -f${NC}"
    echo -e "${BLUE}📁 Application logs are written to: ./logs/${NC}"
else
    echo -e "\n${YELLOW}⚠️  Some services may still be starting up...${NC}"
    echo -e "Check status with: docker-compose ps"
fi