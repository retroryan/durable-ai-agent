import pytest
import asyncio
import httpx
import os


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.skipif(
    os.environ.get("TOOLS_MOCK") != "true",
    reason="MCP tests require TOOLS_MOCK=true"
)
async def test_mcp_tool_execution_in_mock_mode():
    """Test MCP tools work correctly in mock mode"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # Test weather forecast MCP tool
        response = await http_client.post(
            "/chat",
            json={"message": "weather: Get forecast for Chicago using MCP"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response
        result = data["response"]["result"]
        assert "weather" in result.lower() or "forecast" in result.lower()
        assert data["status"] == "completed"
        
        # Test historical weather MCP tool
        response = await http_client.post(
            "/chat",
            json={"message": "weather: Get historical weather for New York"}
        )
        assert response.status_code == 200
        data = response.json()
        result = data["response"]["result"]
        assert any(word in result.lower() for word in ["historical", "weather", "data"])
        
        # Test agricultural conditions MCP tool
        response = await http_client.post(
            "/chat",
            json={"message": "weather: What are the agricultural conditions in Iowa?"}
        )
        assert response.status_code == 200
        data = response.json()
        result = data["response"]["result"]
        assert any(word in result.lower() for word in ["agricultural", "farming", "conditions", "soil"])


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_mcp_error_handling():
    """Test MCP tool error handling"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # Test with invalid location (should handle gracefully)
        response = await http_client.post(
            "/chat",
            json={"message": "weather: Get forecast for InvalidLocation12345"}
        )
        assert response.status_code == 200
        data = response.json()
        # Should still complete even with errors
        assert data["status"] == "completed"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_mixed_tool_execution():
    """Test mixing traditional and MCP tools"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # This query might trigger both traditional and MCP tools
        response = await http_client.post(
            "/chat",
            json={
                "message": "weather: Compare current weather and agricultural conditions in California"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains relevant information
        result = data["response"]["result"]
        assert "california" in result.lower()
        assert any(word in result.lower() for word in ["weather", "agricultural", "conditions"])


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_mcp_tool_selection():
    """Test that the React agent correctly selects MCP tools"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # Query that should trigger MCP forecast tool
        response = await http_client.post(
            "/chat",
            json={"message": "weather: I need a detailed weather forecast for Seattle"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check response quality
        result = data["response"]["result"]
        assert "seattle" in result.lower()
        assert any(word in result.lower() for word in ["forecast", "temperature", "conditions"])
        
        # Query that should trigger MCP agricultural tool
        response = await http_client.post(
            "/chat",
            json={"message": "weather: What crops should I plant in Nebraska?"}
        )
        assert response.status_code == 200
        data = response.json()
        
        result = data["response"]["result"]
        assert any(word in result.lower() for word in ["nebraska", "crop", "plant", "agricultural"])