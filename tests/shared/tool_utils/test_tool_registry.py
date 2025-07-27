"""Tests for tool registry with consolidated MCP tools."""
import pytest

from shared.tool_utils.agriculture_tool_set import AgricultureToolSet
from shared.tool_utils.mcp_tool import MCPTool
from shared.tool_utils.registry import ToolRegistry, create_tool_set_registry


class TestToolRegistryConsolidatedTools:
    """Tests for tool registry with consolidated MCP tools."""
    
    def test_agriculture_tool_set_has_consolidated_tools(self):
        """Test that agriculture tool set includes only consolidated MCP tools."""
        tool_set = AgricultureToolSet()
        tool_classes = tool_set.config.tool_classes
        
        # Should have 3 consolidated tools
        assert len(tool_classes) == 3
        
        # Check consolidated tools are present
        tool_names = [tc.NAME for tc in tool_classes]
        assert "get_weather_forecast" in tool_names
        assert "get_historical_weather" in tool_names
        assert "get_agricultural_conditions" in tool_names
        
        # No _mcp suffix tools
        assert "get_weather_forecast_mcp" not in tool_names
        assert "get_historical_weather_mcp" not in tool_names
        assert "get_agricultural_conditions_mcp" not in tool_names
    
    def test_registry_registers_consolidated_tools(self):
        """Test that tool registry properly registers consolidated MCP tools."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Check all tools are registered
        all_tools = registry.get_all_tools()
        assert len(all_tools) == 3
        
        # Check tools are accessible and are MCP tools
        forecast = registry.get_tool("get_weather_forecast")
        assert forecast is not None
        assert isinstance(forecast, MCPTool)
        assert forecast.__class__.is_mcp is True
        
        historical = registry.get_tool("get_historical_weather")
        assert historical is not None
        assert isinstance(historical, MCPTool)
        assert historical.__class__.is_mcp is True
        
        agricultural = registry.get_tool("get_agricultural_conditions")
        assert agricultural is not None
        assert isinstance(agricultural, MCPTool)
        assert agricultural.__class__.is_mcp is True
    
    def test_consolidated_tools_have_mcp_config(self):
        """Test that consolidated tools have MCP configuration."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Get tools
        forecast = registry.get_tool("get_weather_forecast")
        historical = registry.get_tool("get_historical_weather")
        agricultural = registry.get_tool("get_agricultural_conditions")
        
        # All should have MCP config methods
        assert hasattr(forecast, 'get_mcp_config')
        assert hasattr(historical, 'get_mcp_config')
        assert hasattr(agricultural, 'get_mcp_config')
        
        # Test get_mcp_config returns valid config
        forecast_config = forecast.get_mcp_config()
        assert forecast_config.server_name == "weather-mcp"
        assert forecast_config.tool_name == "get_weather_forecast"  # Unprefixed
        assert forecast_config.server_definition.connection_type == "http"
        assert forecast_config.server_definition.url == "http://localhost:7778/mcp"
    
    def test_tool_registry_clear_removes_all_tools(self):
        """Test that clearing registry removes all consolidated tools."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Verify tools are registered
        assert len(registry.get_all_tools()) == 3
        
        # Clear registry
        registry.clear()
        
        # Verify all tools are removed
        assert len(registry.get_all_tools()) == 0
        assert registry.get_tool("get_weather_forecast") is None
        assert registry.get_tool("get_historical_weather") is None
        assert registry.get_tool("get_agricultural_conditions") is None
    
    def test_mock_mode_affects_tool_execution(self):
        """Test that mock mode affects tool execution behavior."""
        # Create registry with mock enabled
        mock_registry = create_tool_set_registry("agriculture", mock_results=True)
        forecast_mock = mock_registry.get_tool("get_weather_forecast")
        
        # Mock mode should allow execute() to return mock data
        result = forecast_mock.execute(latitude=40.7, longitude=-74.0, days=3)
        assert "Weather Forecast" in result
        assert "40.7" in result
        
        # Create registry with mock disabled
        real_registry = create_tool_set_registry("agriculture", mock_results=False)
        forecast_real = real_registry.get_tool("get_weather_forecast")
        
        # Non-mock mode should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            forecast_real.execute(latitude=40.7, longitude=-74.0, days=3)
        assert "MCP tools should be executed via activity" in str(exc_info.value)