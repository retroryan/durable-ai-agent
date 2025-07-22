"""
MCP-enabled tool base class that extends BaseTool.

This module defines the MCPTool class which adds MCP (Model Context Protocol) 
capabilities to the base tool system without breaking existing functionality.
"""
import os
from abc import ABC
from pathlib import Path
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
        Get MCP configuration for this tool with support for both HTTP and stdio.
        
        Transport selection:
        - When MCP_USE_STDIO=true: Use stdio (direct process communication)
        - Otherwise: Use HTTP transport
        
        Tool name resolution:
        - Stdio mode: Tool names are unprefixed (e.g., "get_weather_forecast")
        - HTTP proxy mode: Tool names are prefixed (e.g., "forecast_get_weather_forecast")
        - HTTP direct mode: Tool names are unprefixed
        
        Returns:
            MCPConfig containing server details and dynamically computed tool name.
        """
        # Check if we should use stdio transport
        use_stdio = os.getenv("MCP_USE_STDIO", "false").lower() == "true"
        
        if use_stdio:
            # Stdio mode: Direct process communication
            # Find the project root by looking for the mcp_servers directory
            current_path = Path(__file__).resolve()
            project_root = current_path.parent.parent.parent  # shared/tool_utils/mcp_tool.py -> project root
            
            # Build path to the MCP server script
            server_script = project_root / "mcp_servers" / f"{self.mcp_server_name}_server.py"
            
            return MCPConfig(
                server_name=self.mcp_server_name,
                tool_name=self.NAME,  # No prefix for stdio
                server_definition=MCPServerDefinition(
                    name=f"{self.mcp_server_name}-stdio",
                    connection_type="stdio",
                    command="python",
                    args=[str(server_script), "--transport", "stdio"],
                    env=None
                )
            )
        else:
            # HTTP mode: Original logic
            use_proxy = os.getenv("MCP_USE_PROXY", "true").lower() == "true"
            
            # Compute tool name based on proxy usage
            if use_proxy:
                # Proxy mode: FastMCP mount() prefixes tool names with server name
                tool_name = f"{self.mcp_server_name}_{self.NAME}"
                url = os.getenv("MCP_URL", "http://weather-proxy:8000/mcp")
            else:
                # Direct mode: Use unprefixed tool name and server-specific URL
                tool_name = self.NAME
                # Map server names to their direct URLs
                server_urls = {
                    "forecast": os.getenv("MCP_FORECAST_URL", "http://localhost:7778/mcp"),
                    "historical": os.getenv("MCP_HISTORICAL_URL", "http://localhost:7779/mcp"),
                    "agricultural": os.getenv("MCP_AGRICULTURAL_URL", "http://localhost:7780/mcp"),
                }
                # Get the URL for this specific server, fallback to MCP_URL if not found
                url = server_urls.get(self.mcp_server_name, os.getenv("MCP_URL", "http://localhost:7778/mcp"))
                
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