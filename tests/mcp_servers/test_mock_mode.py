"""Tests for MCP servers mock mode."""
import json
import os
import subprocess
import time
from typing import Dict, Any
import pytest
import httpx


def start_server(server_module: str, port: int) -> subprocess.Popen:
    """Start an MCP server in mock mode."""
    env = os.environ.copy()
    env["TOOLS_MOCK"] = "true"
    env["MCP_PORT"] = str(port)
    
    process = subprocess.Popen(
        ["poetry", "run", "python", f"mcp_servers/{server_module}.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to start
    time.sleep(2)
    
    return process


async def call_mcp_tool(url: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Call an MCP tool via HTTP."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                },
                "id": 1
            },
            headers={"Content-Type": "application/json"},
            timeout=10.0
        )
        response.raise_for_status()
        result = response.json()
        return result.get("result", {})


@pytest.mark.asyncio
class TestMCPServerMockMode:
    """Tests for MCP servers in mock mode."""
    
    async def test_forecast_server_mock_mode(self):
        """Test forecast server returns mock data."""
        # Start server
        process = start_server("forecast_server", 7778)
        
        try:
            # Call the tool
            result = await call_mcp_tool(
                "http://localhost:7778/mcp",
                "get_weather_forecast",
                {
                    "location": "New York",
                    "days": 3
                }
            )
            
            # Verify mock response
            assert result["mock"] is True
            assert "Mock weather forecast" in result["summary"]
            assert result["location_info"]["name"] == "New York"
            assert len(result["daily"]["time"]) == 3
            assert result["current"]["temperature_2m"] == 18.5
            
        finally:
            process.terminate()
            process.wait()
    
    async def test_historical_server_mock_mode(self):
        """Test historical server returns mock data."""
        # Start server
        process = start_server("historical_server", 7779)
        
        try:
            # Call the tool
            result = await call_mcp_tool(
                "http://localhost:7779/mcp",
                "get_historical_weather",
                {
                    "location": "San Francisco",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-03"
                }
            )
            
            # Verify mock response
            assert result["mock"] is True
            assert "Mock historical weather" in result["summary"]
            assert result["location_info"]["name"] == "San Francisco"
            assert len(result["daily"]["time"]) == 3
            
        finally:
            process.terminate()
            process.wait()
    
    async def test_agricultural_server_mock_mode(self):
        """Test agricultural server returns mock data."""
        # Start server
        process = start_server("agricultural_server", 7780)
        
        try:
            # Call the tool
            result = await call_mcp_tool(
                "http://localhost:7780/mcp",
                "get_agricultural_conditions",
                {
                    "location": "Des Moines",
                    "days": 5,
                    "crop_type": "corn"
                }
            )
            
            # Verify mock response
            assert result["mock"] is True
            assert "Mock agricultural conditions" in result["summary"]
            assert result["location_info"]["name"] == "Des Moines"
            assert len(result["daily"]["time"]) == 5
            assert result["crop_specific"]["crop_type"] == "corn"
            assert result["agricultural_metrics"]["average_soil_moisture"] == 26.9
            
        finally:
            process.terminate()
            process.wait()
    
    async def test_coordinates_work_in_mock_mode(self):
        """Test that direct coordinates work in mock mode."""
        # Start server
        process = start_server("forecast_server", 7778)
        
        try:
            # Call with coordinates
            result = await call_mcp_tool(
                "http://localhost:7778/mcp",
                "get_weather_forecast",
                {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "days": 7
                }
            )
            
            # Verify mock response
            assert result["mock"] is True
            assert result["location_info"]["coordinates"]["latitude"] == 40.7128
            assert result["location_info"]["coordinates"]["longitude"] == -74.0060
            
        finally:
            process.terminate()
            process.wait()