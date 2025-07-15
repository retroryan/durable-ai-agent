"""MCP-enabled historical weather tool that uses the MCP weather proxy service."""
from typing import ClassVar, Type

from pydantic import BaseModel

from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool
from .historical_weather import HistoricalRequest


class HistoricalWeatherMCPTool(MCPTool):
    """Historical weather tool that uses MCP backend service."""
    
    NAME: ClassVar[str] = "get_historical_weather_mcp"
    MODULE: ClassVar[str] = "tools.precision_agriculture.historical_weather_mcp"
    
    description: str = (
        "Get historical weather data for a location using MCP service. "
        "Retrieves past temperature, precipitation, and weather conditions."
    )
    args_model: Type[BaseModel] = HistoricalRequest
    
    # MCP configuration
    mcp_server_name: str = "historical"
    mcp_tool_name: str = "historical_get_historical_weather"
    mcp_server_definition: MCPServerDefinition = MCPServerDefinition(
        name="weather-proxy",
        connection_type="http",
        url="http://weather-proxy:8000/mcp"
    )