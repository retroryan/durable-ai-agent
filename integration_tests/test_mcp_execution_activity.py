"""Integration tests for MCP Execution Activity with mock MCP server."""
import asyncio
import os
from typing import Type
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from activities.mcp_execution_activity import MCPExecutionActivity
from models.tool_definitions import MCPServerDefinition
from models.types import ActivityStatus, ToolExecutionRequest
from shared.tool_utils.mcp_tool import MCPTool
from shared.tool_utils.registry import ToolRegistry
from workflows.test_workflow import TestWorkflow


class WeatherArgs(BaseModel):
    """Arguments for weather MCP tool."""
    latitude: float = Field(description="Latitude")
    longitude: float = Field(description="Longitude")
    days: int = Field(default=7, description="Number of days")


class WeatherForecastMCPTool(MCPTool):
    """Weather forecast tool using MCP."""
    
    NAME = "weather_forecast_mcp"
    MODULE = "tools.weather.mcp"
    
    description: str = "Get weather forecast via MCP"
    args_model: Type[BaseModel] = WeatherArgs
    
    mcp_server_name: str = "forecast"
    mcp_tool_name: str = "forecast_get_weather_forecast"
    mcp_server_definition: MCPServerDefinition = MCPServerDefinition(
        name="weather-proxy",
        connection_type="http",
        url="http://weather-proxy:8000/mcp"
    )


@pytest.mark.asyncio
@pytest.mark.integration
class TestMCPExecutionActivityIntegration:
    """Integration tests for MCP Execution Activity."""
    
    async def test_mcp_activity_with_temporal_worker(self):
        """Test MCP execution activity in a Temporal worker context."""
        # Create tool registry and register MCP tool
        tool_registry = ToolRegistry()
        tool_registry._tools[WeatherForecastMCPTool.NAME] = WeatherForecastMCPTool
        tool_registry._instances[WeatherForecastMCPTool.NAME] = WeatherForecastMCPTool()
        
        # Create activity instance
        mcp_activity = MCPExecutionActivity(tool_registry=tool_registry)
        
        # Mock the MCP client manager to avoid real connections
        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text="Forecast: Sunny, 72°F for 7 days")]
        mock_client.call_tool.return_value = mock_result
        
        async with await WorkflowEnvironment.start_time_skipping() as env:
            with patch.object(
                mcp_activity.mcp_client_manager,
                'get_client',
                return_value=mock_client
            ):
                # Create worker with the activity
                async with Worker(
                    env.client,
                    task_queue="test-mcp-queue",
                    workflows=[TestWorkflow],
                    activities=[mcp_activity.execute_mcp_tool],
                ):
                    # Execute workflow that calls the activity
                    handle = await env.client.start_workflow(
                        TestWorkflow.run,
                        ToolExecutionRequest(
                            tool_name="weather_forecast_mcp",
                            tool_args={"latitude": 37.7749, "longitude": -122.4194, "days": 7},
                            trajectory={"thought_0": "Need weather forecast"},
                            current_iteration=1
                        ),
                        id="test-mcp-workflow",
                        task_queue="test-mcp-queue",
                    )
                    
                    result = await handle.result()
                    
                    # Verify results
                    assert result["status"] == ActivityStatus.SUCCESS
                    assert "Forecast: Sunny, 72°F for 7 days" in result["trajectory"]["observation_0"]
                    assert "thought_0" in result["trajectory"]
                    
                    # Verify MCP client was called
                    mock_client.call_tool.assert_called_once_with(
                        name="forecast_get_weather_forecast",
                        arguments={"latitude": 37.7749, "longitude": -122.4194, "days": 7}
                    )
    
    @pytest.mark.skipif(
        os.getenv("MCP_PROXY_AVAILABLE") != "true",
        reason="MCP proxy not available"
    )
    async def test_mcp_activity_with_real_proxy(self):
        """Test MCP execution activity with real MCP proxy (when available)."""
        # Create tool registry and register MCP tool
        tool_registry = ToolRegistry()
        tool_registry._tools[WeatherForecastMCPTool.NAME] = WeatherForecastMCPTool
        tool_registry._instances[WeatherForecastMCPTool.NAME] = WeatherForecastMCPTool()
        
        # Create activity instance (no mocking)
        mcp_activity = MCPExecutionActivity(tool_registry=tool_registry)
        
        # Create request
        request = ToolExecutionRequest(
            tool_name="weather_forecast_mcp",
            tool_args={"latitude": 37.7749, "longitude": -122.4194, "days": 3},
            trajectory={"thought_0": "Need weather forecast"},
            current_iteration=1
        )
        
        # Execute directly
        result = await mcp_activity.execute_mcp_tool(request)
        
        # Verify structure (actual data will vary)
        assert result["status"] == ActivityStatus.SUCCESS
        assert "observation_0" in result["trajectory"]
        assert "thought_0" in result["trajectory"]
        
        # Cleanup
        await mcp_activity.cleanup()