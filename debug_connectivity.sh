#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Debugging Docker Connectivity${NC}"
echo "========================================="

# Check if containers are running
echo -e "\n${YELLOW}1. Checking container status:${NC}"
docker-compose ps

# Check docker network
echo -e "\n${YELLOW}2. Checking docker network:${NC}"
docker network ls | grep durable

# Test internal connectivity from frontend to api
echo -e "\n${YELLOW}3. Testing frontend -> api connectivity:${NC}"
if docker-compose exec frontend ping -c 3 api 2>/dev/null; then
    echo -e "${GREEN}✓ Frontend can ping API container${NC}"
else
    echo -e "${RED}✗ Frontend cannot ping API container${NC}"
fi

# Test if API is responding internally
echo -e "\n${YELLOW}4. Testing API health endpoint from frontend container:${NC}"
if docker-compose exec frontend wget -q --spider http://api:8000/health 2>/dev/null; then
    echo -e "${GREEN}✓ API health endpoint is accessible from frontend${NC}"
else
    echo -e "${RED}✗ API health endpoint is NOT accessible from frontend${NC}"
fi

# Test API from host
echo -e "\n${YELLOW}5. Testing API from host:${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ API is accessible from host${NC}"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo -e "${RED}✗ API is NOT accessible from host${NC}"
fi

# Check nginx logs
echo -e "\n${YELLOW}6. Recent nginx error logs:${NC}"
docker-compose logs --tail=10 frontend 2>/dev/null || echo "No nginx logs available"

# Check API logs
echo -e "\n${YELLOW}7. Recent API logs:${NC}"
docker-compose logs --tail=10 api 2>/dev/null || echo "No API logs available"

echo -e "\n${BLUE}🔍 Debug complete. Check the results above for connectivity issues.${NC}"