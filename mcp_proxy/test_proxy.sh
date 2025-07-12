#!/bin/bash
# Simple test script for MCP Proxy

echo "Testing MCP Proxy..."
echo "==================="

# Test health endpoint
echo -e "\n1. Testing health endpoint..."
curl -s http://localhost:8000/health | python -m json.tool

# Test root endpoint
echo -e "\n2. Testing root endpoint..."
curl -s http://localhost:8000/ | python -m json.tool

# Test forecast service - list tools
echo -e "\n3. Testing forecast service (list tools)..."
curl -s -X POST http://localhost:8000/mcp/forecast \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m json.tool

# Test current weather service - list tools
echo -e "\n4. Testing current weather service (list tools)..."
curl -s -X POST http://localhost:8000/mcp/current \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python -m json.tool

# Test invalid service (should return 404)
echo -e "\n5. Testing invalid service (should fail)..."
curl -s -X POST http://localhost:8000/mcp/invalid \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/list","params":{}}' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\nTests complete!"