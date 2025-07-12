#!/bin/bash
# Simple script to stop and remove the MCP proxy Docker container

echo "Stopping MCP Proxy container..."
docker stop mcp-proxy

echo "Removing MCP Proxy container..."
docker rm mcp-proxy

echo "✅ MCP Proxy container stopped and removed"