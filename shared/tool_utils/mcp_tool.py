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
    
    All MCP tools connect to the MCP server on port 7778.
    Tool names are always unprefixed (e.g., "get_weather_forecast").
    """
    
    # Override the class-level indicator for MCP tools
    is_mcp: ClassVar[bool] = True  # MCP tools are identified by this class variable
    
    # MCP configuration fields
    
    # Server definition is computed in get_mcp_config()
    mcp_server_definition: Optional[MCPServerDefinition] = Field(None, exclude=True)
    
    def get_mcp_config(self) -> MCPConfig:
        """
        Get MCP configuration for this tool via HTTP transport.
        
        Tool names are always unprefixed (e.g., "get_weather_forecast").
        
        Returns:
            MCPConfig containing server details and tool name.
        """
        # Single server URL for all agriculture tools
        url = os.getenv("MCP_SERVER_URL", "http://localhost:7778/mcp")
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"MCPTool.get_mcp_config: MCP_SERVER_URL from env: {url}")
        
        return MCPConfig(
            server_name="weather-mcp",
            tool_name=self.NAME,  # Always use unprefixed tool name
            server_definition=MCPServerDefinition(
                name="weather-mcp",
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