"""MCP-enabled weather forecast tool that uses the MCP weather proxy service."""
from typing import ClassVar, Type

from pydantic import BaseModel

from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool
from .weather_forecast import ForecastRequest


class WeatherForecastMCPTool(MCPTool):
    """Weather forecast tool that uses MCP backend service."""
    
    NAME: ClassVar[str] = "get_weather_forecast_mcp"
    MODULE: ClassVar[str] = "tools.precision_agriculture.weather_forecast_mcp"
    
    description: str = (
        "Get weather forecast for a location using MCP service. Includes temperature, "
        "precipitation, wind, and other meteorological conditions from the weather proxy."
    )
    args_model: Type[BaseModel] = ForecastRequest
    
    # MCP configuration
    mcp_server_name: str = "forecast"
    mcp_tool_name: str = "forecast_get_weather_forecast"
    mcp_server_definition: MCPServerDefinition = MCPServerDefinition(
        name="weather-proxy",
        connection_type="http",
        url="http://weather-proxy:8000/mcp"
    )