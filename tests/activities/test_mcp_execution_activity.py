"""Tests for MCP Execution Activity."""
from typing import Type
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from activities.mcp_execution_activity import MCPExecutionActivity
from models.tool_definitions import MCPServerDefinition
from models.types import ActivityStatus, ToolExecutionRequest
from shared.tool_utils.mcp_tool import MCPTool
from shared.tool_utils.registry import ToolRegistry


class TestMCPToolArgs(BaseModel):
    """Test arguments for MCP tool."""
    location: str = Field(description="Location to query")
    days: int = Field(default=7, description="Number of days")


class TestMCPTool(MCPTool):
    """Test MCP tool for testing."""
    
    NAME = "test_mcp_weather"
    MODULE = "test.mcp.weather"
    
    description: str = "Test MCP weather tool"
    args_model: Type[BaseModel] = TestMCPToolArgs
    
    mcp_server_name: str = "weather"
    mcp_tool_name: str = "get_weather"
    mcp_server_definition: MCPServerDefinition = MCPServerDefinition(
        name="weather-server",
        connection_type="http",
        url="http://localhost:8000/mcp"
    )


@pytest.mark.asyncio
class TestMCPExecutionActivity:
    """Tests for MCP Execution Activity."""
    
    async def test_execute_mcp_tool_success(self):
        """Test successful MCP tool execution."""
        # Setup
        tool_registry = ToolRegistry()
        # Manually register the tool
        tool_registry._tools[TestMCPTool.NAME] = TestMCPTool
        tool_registry._instances[TestMCPTool.NAME] = TestMCPTool()
        
        activity = MCPExecutionActivity(tool_registry=tool_registry)
        
        # Mock MCP client manager
        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text="Weather: Sunny, 72°F")]
        mock_client.call_tool.return_value = mock_result
        
        with patch.object(
            activity.mcp_client_manager, 
            'get_client', 
            return_value=mock_client
        ):
            # Create request
            request = ToolExecutionRequest(
                tool_name="test_mcp_weather",
                tool_args={"location": "San Francisco", "days": 3},
                trajectory={"thought_0": "Need weather info"},
                current_iteration=1
            )
            
            # Execute
            result = await activity.execute_mcp_tool(request)
            
            # Verify
            assert result["status"] == ActivityStatus.SUCCESS
            assert result["trajectory"]["observation_0"] == "Weather: Sunny, 72°F"
            assert "thought_0" in result["trajectory"]
            
            # Verify MCP client was called correctly
            mock_client.call_tool.assert_called_once_with(
                name="get_weather",
                arguments={"location": "San Francisco", "days": 3}
            )
    
    async def test_execute_mcp_tool_no_registry(self):
        """Test MCP tool execution without registry."""
        activity = MCPExecutionActivity(tool_registry=None)
        
        request = ToolExecutionRequest(
            tool_name="test_tool",
            tool_args={},
            trajectory={},
            current_iteration=1
        )
        
        result = await activity.execute_mcp_tool(request)
        
        assert result["status"] == ActivityStatus.ERROR
        assert "not properly initialized with tool_registry" in result["error"]
        assert "Tool registry not initialized" in result["trajectory"]["observation_0"]
    
    async def test_execute_non_mcp_tool_error(self):
        """Test error when trying to execute non-MCP tool."""
        # Setup with a non-MCP tool
        tool_registry = ToolRegistry()
        
        # Mock a non-MCP tool
        mock_tool = MagicMock()
        mock_tool.NAME = "regular_tool"
        tool_registry._tools = {"regular_tool": mock_tool}
        
        activity = MCPExecutionActivity(tool_registry=tool_registry)
        
        request = ToolExecutionRequest(
            tool_name="regular_tool",
            tool_args={},
            trajectory={},
            current_iteration=1
        )
        
        result = await activity.execute_mcp_tool(request)
        
        assert result["status"] == ActivityStatus.ERROR
        assert "not an MCP tool" in result["error"]
        assert "not an MCP tool" in result["trajectory"]["observation_0"]
    
    async def test_execute_mcp_tool_client_error(self):
        """Test MCP tool execution with client error."""
        # Setup
        tool_registry = ToolRegistry()
        # Manually register the tool
        tool_registry._tools[TestMCPTool.NAME] = TestMCPTool
        tool_registry._instances[TestMCPTool.NAME] = TestMCPTool()
        
        activity = MCPExecutionActivity(tool_registry=tool_registry)
        
        # Mock client error
        with patch.object(
            activity.mcp_client_manager,
            'get_client',
            side_effect=Exception("Connection failed")
        ):
            request = ToolExecutionRequest(
                tool_name="test_mcp_weather",
                tool_args={"location": "NYC"},
                trajectory={},
                current_iteration=1
            )
            
            result = await activity.execute_mcp_tool(request)
            
            assert result["status"] == ActivityStatus.ERROR
            assert "Connection failed" in result["error"]
            assert "Connection failed" in result["trajectory"]["observation_0"]
    
    async def test_execute_mcp_tool_call_error(self):
        """Test MCP tool execution with tool call error."""
        # Setup
        tool_registry = ToolRegistry()
        # Manually register the tool
        tool_registry._tools[TestMCPTool.NAME] = TestMCPTool
        tool_registry._instances[TestMCPTool.NAME] = TestMCPTool()
        
        activity = MCPExecutionActivity(tool_registry=tool_registry)
        
        # Mock client that fails on call_tool
        mock_client = AsyncMock()
        mock_client.call_tool.side_effect = Exception("API error")
        
        with patch.object(
            activity.mcp_client_manager,
            'get_client',
            return_value=mock_client
        ):
            request = ToolExecutionRequest(
                tool_name="test_mcp_weather",
                tool_args={"location": "LA"},
                trajectory={},
                current_iteration=1
            )
            
            result = await activity.execute_mcp_tool(request)
            
            assert result["status"] == ActivityStatus.ERROR
            assert "API error" in result["error"]
            assert "API error" in result["trajectory"]["observation_0"]
    
    async def test_execute_mcp_tool_empty_result(self):
        """Test MCP tool execution with empty result."""
        # Setup
        tool_registry = ToolRegistry()
        # Manually register the tool
        tool_registry._tools[TestMCPTool.NAME] = TestMCPTool
        tool_registry._instances[TestMCPTool.NAME] = TestMCPTool()
        
        activity = MCPExecutionActivity(tool_registry=tool_registry)
        
        # Mock client with empty result
        mock_client = AsyncMock()
        mock_result = MagicMock()
        mock_result.content = []
        mock_client.call_tool.return_value = mock_result
        
        with patch.object(
            activity.mcp_client_manager,
            'get_client',
            return_value=mock_client
        ):
            request = ToolExecutionRequest(
                tool_name="test_mcp_weather",
                tool_args={"location": "Boston"},
                trajectory={"thought_0": "Check weather"},
                current_iteration=1
            )
            
            result = await activity.execute_mcp_tool(request)
            
            assert result["status"] == ActivityStatus.SUCCESS
            assert result["trajectory"]["observation_0"] == "No result"
    
    async def test_cleanup(self):
        """Test cleanup method."""
        activity = MCPExecutionActivity()
        
        # Mock cleanup
        with patch.object(
            activity.mcp_client_manager,
            'cleanup',
            new_callable=AsyncMock
        ) as mock_cleanup:
            await activity.cleanup()
            mock_cleanup.assert_called_once()