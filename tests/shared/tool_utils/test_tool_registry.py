"""Tests for tool registry with MCP tools integration."""
import pytest

from shared.tool_utils.agriculture_tool_set import AgricultureToolSet
from shared.tool_utils.mcp_tool import MCPTool
from shared.tool_utils.registry import ToolRegistry, create_tool_set_registry


class TestToolRegistryMCPIntegration:
    """Tests for tool registry with MCP tools."""
    
    def test_agriculture_tool_set_includes_mcp_tools(self):
        """Test that agriculture tool set includes both traditional and MCP tools."""
        tool_set = AgricultureToolSet()
        tool_classes = tool_set.config.tool_classes
        
        # Should have 6 tools total (3 traditional + 3 MCP)
        assert len(tool_classes) == 6
        
        # Check traditional tools are present
        tool_names = [tc.NAME for tc in tool_classes]
        assert "get_weather_forecast" in tool_names
        assert "get_historical_weather" in tool_names
        assert "get_agricultural_conditions" in tool_names
        
        # Check MCP tools are present
        assert "get_weather_forecast_mcp" in tool_names
        assert "get_historical_weather_mcp" in tool_names
        assert "get_agricultural_conditions_mcp" in tool_names
    
    def test_registry_registers_mcp_tools(self):
        """Test that tool registry properly registers MCP tools."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Check all tools are registered
        all_tools = registry.get_all_tools()
        assert len(all_tools) == 6
        
        # Check MCP tools are accessible
        forecast_mcp = registry.get_tool("get_weather_forecast_mcp")
        assert forecast_mcp is not None
        assert isinstance(forecast_mcp, MCPTool)
        assert forecast_mcp.uses_mcp is True
        
        historical_mcp = registry.get_tool("get_historical_weather_mcp")
        assert historical_mcp is not None
        assert isinstance(historical_mcp, MCPTool)
        assert historical_mcp.uses_mcp is True
        
        agricultural_mcp = registry.get_tool("get_agricultural_conditions_mcp")
        assert agricultural_mcp is not None
        assert isinstance(agricultural_mcp, MCPTool)
        assert agricultural_mcp.uses_mcp is True
    
    def test_registry_distinguishes_tool_types(self):
        """Test that registry can distinguish between traditional and MCP tools."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Get traditional tool
        traditional_forecast = registry.get_tool("get_weather_forecast")
        assert traditional_forecast is not None
        assert not isinstance(traditional_forecast, MCPTool)
        assert traditional_forecast.uses_mcp is False
        
        # Get MCP tool
        mcp_forecast = registry.get_tool("get_weather_forecast_mcp")
        assert mcp_forecast is not None
        assert isinstance(mcp_forecast, MCPTool)
        assert mcp_forecast.uses_mcp is True
    
    def test_react_agent_can_select_mcp_tools(self):
        """Test that React agent can select MCP tools from registry."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Get all tool names
        tool_names = registry.get_tool_names()
        
        # Both tool types should be available for selection
        assert "get_weather_forecast" in tool_names
        assert "get_weather_forecast_mcp" in tool_names
        
        # React agent should be able to choose based on tool descriptions
        traditional_tool = registry.get_tool("get_weather_forecast")
        mcp_tool = registry.get_tool("get_weather_forecast_mcp")
        
        # Descriptions should be different to help agent choose
        assert "mcp" not in traditional_tool.description.lower()
        assert "mcp" in mcp_tool.description.lower()
    
    def test_tool_registry_clear_includes_mcp_tools(self):
        """Test that clearing registry removes all tools including MCP."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Verify tools are registered
        assert len(registry.get_all_tools()) == 6
        
        # Clear registry
        registry.clear()
        
        # Verify all tools are removed
        assert len(registry.get_all_tools()) == 0
        assert registry.get_tool("get_weather_forecast") is None
        assert registry.get_tool("get_weather_forecast_mcp") is None