"""
Simple integration tests for MCP Proxy.

Run with: pytest mcp_proxy/tests/test_integration.py
"""

from typing import Any, Dict

import httpx
import pytest


class TestMCPProxy:
    """Basic integration tests for the proxy."""

    base_url = "http://localhost:8000"

    @pytest.fixture
    def client(self):
        """Create HTTP client."""
        return httpx.Client(base_url=self.base_url, timeout=10.0)

    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "services" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "MCP Weather Proxy"
        assert "services" in data
        assert len(data["services"]) == 3

    def test_list_tools_forecast(self, client):
        """Test listing tools from forecast service."""
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

        response = client.post("/mcp/forecast", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data.get("jsonrpc") == "2.0"
        assert "result" in data or "error" in data

    def test_list_tools_current(self, client):
        """Test listing tools from current weather service."""
        request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

        response = client.post("/mcp/current", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data.get("jsonrpc") == "2.0"

    def test_invalid_service(self, client):
        """Test request to invalid service returns 404."""
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

        response = client.post("/mcp/invalid", json=request)
        assert response.status_code == 404

    def test_tool_call(self, client):
        """Test calling a tool through the proxy."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "get_current_weather",
                "arguments": {"location": "Melbourne"},
            },
        }

        response = client.post("/mcp/current", json=request)
        assert response.status_code == 200

        data = response.json()
        assert data.get("jsonrpc") == "2.0"


if __name__ == "__main__":
    # Run basic smoke test
    print("Running basic MCP Proxy tests...")

    with httpx.Client(base_url="http://localhost:8000", timeout=5.0) as client:
        try:
            # Test health
            response = client.get("/health")
            print(f"Health check: {response.status_code}")
            print(f"Response: {response.json()}")

            # Test root
            response = client.get("/")
            print(f"\nRoot endpoint: {response.status_code}")
            print(f"Response: {response.json()}")

            # Test MCP request
            request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
            response = client.post("/mcp/forecast", json=request)
            print(f"\nMCP request to forecast: {response.status_code}")
            print(f"Response: {response.json()}")

        except Exception as e:
            print(f"Error: {e}")
            print("Make sure the proxy server is running on port 8000")
