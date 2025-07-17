"""
MCP-enabled tool base class that extends BaseTool.

This module defines the MCPTool class which adds MCP (Model Context Protocol) 
capabilities to the base tool system without breaking existing functionality.
"""
import os
from abc import ABC
from typing import ClassVar, Optional

from pydantic import Field

from models.types import MCPConfig
from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.base_tool import BaseTool


class MCPTool(BaseTool, ABC):
    """
    Base class for tools that use MCP servers as their backend.
    
    This class extends BaseTool to add MCP-specific configuration while
    maintaining full compatibility with the existing tool system.
    
    IMPORTANT NAMING CONVENTION:
    - Tool.NAME: The canonical tool identifier (e.g., "get_weather_forecast")
    - mcp_server_name: Identifies which MCP server to connect to (e.g., "forecast")
    - Tool names in MCP calls depend on deployment mode:
      * When using proxy (MCP_USE_PROXY=true): Tool names are prefixed with server name
        Example: "forecast_get_weather_forecast"
      * When using direct connection (MCP_USE_PROXY=false): Tool names are unprefixed
        Example: "get_weather_forecast"
    
    This dynamic naming handles the fact that FastMCP's mount() feature automatically
    prefixes tool names when mounting services in the proxy.
    """
    
    # Override the class-level indicator for MCP tools
    is_mcp: ClassVar[bool] = True  # MCP tools are identified by this class variable
    
    # MCP configuration fields
    # mcp_server_name identifies which MCP server this tool connects to
    # Examples: "forecast", "historical", "agricultural"
    mcp_server_name: str = Field(..., exclude=True)
    
    # Note: mcp_tool_name has been removed - it's computed dynamically in get_mcp_config()
    # based on whether we're using the proxy or direct connection
    
    mcp_server_definition: Optional[MCPServerDefinition] = Field(None, exclude=True)
    
    def get_mcp_config(self) -> MCPConfig:
        """
        Get MCP configuration for this tool with dynamic tool name resolution.
        
        The tool name is computed based on the MCP_USE_PROXY environment variable:
        - When using proxy (default): Tool names are prefixed with the server name
          because FastMCP's mount() feature adds these prefixes automatically
        - When using direct connection: Tool names are used as-is (unprefixed)
        
        Returns:
            MCPConfig containing server details and dynamically computed tool name.
        """
        # Determine if we're using the proxy based on environment variable
        # Default to true for backward compatibility with docker-compose setup
        use_proxy = os.getenv("MCP_USE_PROXY", "true").lower() == "true"
        
        # Get URL from environment (this already handles proxy vs direct URLs)
        # Example proxy URL: http://weather-proxy:8000/mcp
        # Example direct URL: http://forecast-server:7778/mcp
        url = os.getenv("MCP_URL", "http://weather-proxy:8000/mcp")
        
        # Compute tool name based on proxy usage
        # IMPORTANT: This handles the naming mismatch between proxy and direct modes
        if use_proxy:
            # Proxy mode: FastMCP mount() prefixes tool names with server name
            # Example: "forecast" + "_" + "get_weather_forecast" = "forecast_get_weather_forecast"
            tool_name = f"{self.mcp_server_name}_{self.NAME}"
        else:
            # Direct mode: Use unprefixed tool name
            # Example: "get_weather_forecast"
            tool_name = self.NAME
            
        return MCPConfig(
            server_name=self.mcp_server_name,
            tool_name=tool_name,
            server_definition=MCPServerDefinition(
                name=f"mcp-{self.mcp_server_name}",
                connection_type="http",
                url=url
            )
        )
    
    def execute(self, **kwargs) -> str:
        """
        MCP tools don't execute locally - they're executed via MCPExecutionActivity.
        
        This method should not be called directly for MCP tools. Instead, the
        workflow routes MCP tools to the MCPExecutionActivity for remote execution.
        
        Raises:
            RuntimeError: Always, as MCP tools should be executed via activity.
        """
        raise RuntimeError(
            f"MCP tool '{self.NAME}' should be executed via activity, "
            "not called directly."
        )