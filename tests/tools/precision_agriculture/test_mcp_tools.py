"""Tests for MCP-enabled weather tools."""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.tool_definitions import MCPServerDefinition
from tools.precision_agriculture.agricultural_weather_mcp import AgriculturalWeatherMCPTool
from tools.precision_agriculture.historical_weather_mcp import HistoricalWeatherMCPTool
from tools.precision_agriculture.weather_forecast_mcp import WeatherForecastMCPTool


class TestMCPWeatherTools:
    """Tests for MCP weather tool implementations."""
    
    def test_weather_forecast_mcp_tool_creation(self):
        """Test WeatherForecastMCPTool can be created with correct configuration."""
        tool = WeatherForecastMCPTool()
        
        assert tool.NAME == "get_weather_forecast_mcp"
        assert tool.MODULE == "tools.precision_agriculture.weather_forecast_mcp"
        assert tool.uses_mcp is True
        assert tool.mcp_server_name == "forecast"
        assert tool.mcp_tool_name == "forecast_get_weather_forecast"
        assert tool.mcp_server_definition.name == "weather-proxy"
        assert tool.mcp_server_definition.connection_type == "http"
        assert tool.mcp_server_definition.url == "http://weather-proxy:8000/mcp"
        assert "forecast" in tool.description.lower()
        assert "mcp" in tool.description.lower()
    
    def test_historical_weather_mcp_tool_creation(self):
        """Test HistoricalWeatherMCPTool can be created with correct configuration."""
        tool = HistoricalWeatherMCPTool()
        
        assert tool.NAME == "get_historical_weather_mcp"
        assert tool.MODULE == "tools.precision_agriculture.historical_weather_mcp"
        assert tool.uses_mcp is True
        assert tool.mcp_server_name == "historical"
        assert tool.mcp_tool_name == "historical_get_historical_weather"
        assert tool.mcp_server_definition.name == "weather-proxy"
        assert tool.mcp_server_definition.connection_type == "http"
        assert tool.mcp_server_definition.url == "http://weather-proxy:8000/mcp"
        assert "historical" in tool.description.lower()
        assert "mcp" in tool.description.lower()
    
    def test_agricultural_weather_mcp_tool_creation(self):
        """Test AgriculturalWeatherMCPTool can be created with correct configuration."""
        tool = AgriculturalWeatherMCPTool()
        
        assert tool.NAME == "get_agricultural_conditions_mcp"
        assert tool.MODULE == "tools.precision_agriculture.agricultural_weather_mcp"
        assert tool.uses_mcp is True
        assert tool.mcp_server_name == "agricultural"
        assert tool.mcp_tool_name == "agricultural_get_agricultural_conditions"
        assert tool.mcp_server_definition.name == "weather-proxy"
        assert tool.mcp_server_definition.connection_type == "http"
        assert tool.mcp_server_definition.url == "http://weather-proxy:8000/mcp"
        assert "agricultural" in tool.description.lower()
        assert "mcp" in tool.description.lower()
    
    def test_mcp_tools_inherit_argument_models(self):
        """Test that MCP tools properly inherit argument models from base tools."""
        forecast_tool = WeatherForecastMCPTool()
        historical_tool = HistoricalWeatherMCPTool()
        agricultural_tool = AgriculturalWeatherMCPTool()
        
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
    
    def test_mcp_tool_execute_raises_error(self):
        """Test that MCP tools raise RuntimeError when execute is called directly."""
        tool = WeatherForecastMCPTool()
        
        with pytest.raises(RuntimeError) as exc_info:
            tool.execute(latitude=40.7128, longitude=-74.0060, days=7)
        
        assert "get_weather_forecast_mcp" in str(exc_info.value)
        assert "MCPExecutionActivity" in str(exc_info.value)
    
    def test_mcp_tool_get_config(self):
        """Test get_mcp_config returns correct configuration."""
        tool = WeatherForecastMCPTool()
        config = tool.get_mcp_config()
        
        assert config["server_name"] == "forecast"
        assert config["tool_name"] == "forecast_get_weather_forecast"
        assert isinstance(config["server_definition"], MCPServerDefinition)
        assert config["server_definition"].name == "weather-proxy"
    
    @pytest.mark.parametrize("mock_setting", ["true", "false"])
    def test_mcp_tools_respect_mock_environment(self, mock_setting):
        """Test that MCP tools work with TOOLS_MOCK environment variable."""
        # Set environment variable
        os.environ["TOOLS_MOCK"] = mock_setting
        
        # Create tools
        forecast_tool = WeatherForecastMCPTool()
        historical_tool = HistoricalWeatherMCPTool()
        agricultural_tool = AgriculturalWeatherMCPTool()
        
        # MCP tools should always use MCP regardless of TOOLS_MOCK
        # The mocking happens at the MCP server level, not the tool level
        assert forecast_tool.uses_mcp is True
        assert historical_tool.uses_mcp is True
        assert agricultural_tool.uses_mcp is True
        
        # Clean up
        if "TOOLS_MOCK" in os.environ:
            del os.environ["TOOLS_MOCK"]