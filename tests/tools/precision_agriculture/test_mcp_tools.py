"""Tests for consolidated MCP-enabled weather tools."""
import os
from unittest.mock import patch

import pytest

from models.tool_definitions import MCPServerDefinition
from models.types import MCPConfig
from tools.precision_agriculture.agricultural_weather import AgriculturalWeatherTool
from tools.precision_agriculture.historical_weather import HistoricalWeatherTool
from tools.precision_agriculture.weather_forecast import WeatherForecastTool


class TestConsolidatedMCPTools:
    """Tests for consolidated MCP weather tool implementations."""
    
    def test_weather_forecast_tool_is_mcp(self):
        """Test WeatherForecastTool is correctly configured as MCP tool."""
        tool = WeatherForecastTool()
        
        assert tool.NAME == "get_weather_forecast"
        assert tool.MODULE == "tools.precision_agriculture.weather_forecast"
        assert tool.__class__.is_mcp is True
        assert tool.mcp_server_name == "forecast"
        # Note: mcp_tool_name has been removed - tool names are now computed dynamically
        assert "forecast" in tool.description.lower()
    
    def test_historical_weather_tool_is_mcp(self):
        """Test HistoricalWeatherTool is correctly configured as MCP tool."""
        tool = HistoricalWeatherTool()
        
        assert tool.NAME == "get_historical_weather"
        assert tool.MODULE == "tools.precision_agriculture.historical_weather"
        assert tool.__class__.is_mcp is True
        assert tool.mcp_server_name == "historical"
        # Note: mcp_tool_name has been removed - tool names are now computed dynamically
        assert "historical" in tool.description.lower()
    
    def test_agricultural_weather_tool_is_mcp(self):
        """Test AgriculturalWeatherTool is correctly configured as MCP tool."""
        tool = AgriculturalWeatherTool()
        
        assert tool.NAME == "get_agricultural_conditions"
        assert tool.MODULE == "tools.precision_agriculture.agricultural_weather"
        assert tool.__class__.is_mcp is True
        assert tool.mcp_server_name == "agricultural"
        # Note: mcp_tool_name has been removed - tool names are now computed dynamically
        assert "agricultural" in tool.description.lower()
    
    def test_tools_have_correct_argument_models(self):
        """Test that tools have proper argument models."""
        forecast_tool = WeatherForecastTool()
        historical_tool = HistoricalWeatherTool()
        agricultural_tool = AgriculturalWeatherTool()
        
        # Check forecast tool arguments
        forecast_args = forecast_tool.get_argument_list()
        assert "latitude" in forecast_args
        assert "longitude" in forecast_args
        assert "days" in forecast_args
        
        # Check historical tool arguments
        historical_args = historical_tool.get_argument_list()
        assert "latitude" in historical_args
        assert "longitude" in historical_args
        assert "start_date" in historical_args
        assert "end_date" in historical_args
        
        # Check agricultural tool arguments
        agricultural_args = agricultural_tool.get_argument_list()
        assert "latitude" in agricultural_args
        assert "longitude" in agricultural_args
        assert "days" in agricultural_args
        assert "crop_type" in agricultural_args
    
    def test_mcp_tool_execute_raises_error_when_not_mocked(self):
        """Test that MCP tools raise RuntimeError when execute is called directly without mocking."""
        tool = WeatherForecastTool(mock_results=False)
        
        with pytest.raises(RuntimeError) as exc_info:
            tool.execute(latitude=40.7128, longitude=-74.0060, days=7)
        
        assert "MCP tools should be executed via activity" in str(exc_info.value)
    
    def test_mcp_tool_execute_returns_mock_when_mocked(self):
        """Test that MCP tools return mock results when mock_results is True."""
        tool = WeatherForecastTool(mock_results=True)
        
        result = tool.execute(latitude=40.7128, longitude=-74.0060, days=7)
        
        assert "Weather Forecast" in result
        assert "40.7128" in result
        assert "-74.0060" in result
    
    @patch.dict(os.environ, {"MCP_USE_PROXY": "true"})
    def test_get_mcp_config_returns_correct_configuration_proxy_mode(self):
        """Test get_mcp_config returns correct configuration in proxy mode."""
        tool = WeatherForecastTool()
        config = tool.get_mcp_config()
        
        assert isinstance(config, MCPConfig)
        assert config.server_name == "forecast"
        # In proxy mode, tool name should be prefixed with server name
        assert config.tool_name == "forecast_get_weather_forecast"
        assert isinstance(config.server_definition, MCPServerDefinition)
        assert config.server_definition.name == "mcp-forecast"
        assert config.server_definition.connection_type == "http"
    
    @patch.dict(os.environ, {"MCP_USE_PROXY": "false"})
    def test_get_mcp_config_returns_correct_configuration_direct_mode(self):
        """Test get_mcp_config returns correct configuration in direct mode."""
        tool = WeatherForecastTool()
        config = tool.get_mcp_config()
        
        assert isinstance(config, MCPConfig)
        assert config.server_name == "forecast"
        # In direct mode, tool name should NOT be prefixed
        assert config.tool_name == "get_weather_forecast"
        assert isinstance(config.server_definition, MCPServerDefinition)
        assert config.server_definition.name == "mcp-forecast"
        assert config.server_definition.connection_type == "http"
    
    @patch.dict(os.environ, {"MCP_URL": "http://custom-mcp:9000/api"})
    def test_mcp_config_uses_environment_url(self):
        """Test that MCP configuration uses MCP_URL from environment."""
        tool = WeatherForecastTool()
        config = tool.get_mcp_config()
        
        assert config.server_definition.url == "http://custom-mcp:9000/api"
    
    def test_mcp_config_uses_default_url_when_not_set(self):
        """Test that MCP configuration uses default URL when MCP_URL not set."""
        # Ensure MCP_URL is not set
        if "MCP_URL" in os.environ:
            del os.environ["MCP_URL"]
        
        tool = WeatherForecastTool()
        config = tool.get_mcp_config()
        
        assert config.server_definition.url == "http://weather-proxy:8000/mcp"