"""MCP-enabled agricultural weather tool that uses the MCP weather proxy service."""
from typing import ClassVar, Type

from pydantic import BaseModel

from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool
from .agricultural_weather import AgriculturalRequest


class AgriculturalWeatherMCPTool(MCPTool):
    """Agricultural weather tool that uses MCP backend service."""
    
    NAME: ClassVar[str] = "get_agricultural_conditions_mcp"
    MODULE: ClassVar[str] = "tools.precision_agriculture.agricultural_weather_mcp"
    
    description: str = (
        "Get agricultural weather conditions using MCP service. Includes soil moisture, "
        "evapotranspiration, and crop growing conditions from the weather proxy."
    )
    args_model: Type[BaseModel] = AgriculturalRequest
    
    # MCP configuration
    mcp_server_name: str = "agricultural"
    mcp_tool_name: str = "agricultural_get_agricultural_conditions"
    mcp_server_definition: MCPServerDefinition = MCPServerDefinition(
        name="weather-proxy",
        connection_type="http",
        url="http://weather-proxy:8000/mcp"
    )