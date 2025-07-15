"""
MCP-enabled tool base class that extends BaseTool.

This module defines the MCPTool class which adds MCP (Model Context Protocol) 
capabilities to the base tool system without breaking existing functionality.
"""
from abc import ABC
from typing import ClassVar, Dict, Optional

from pydantic import Field

from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.base_tool import BaseTool


class MCPTool(BaseTool, ABC):
    """
    Base class for tools that use MCP servers as their backend.
    
    This class extends BaseTool to add MCP-specific configuration while
    maintaining full compatibility with the existing tool system.
    """
    
    # MCP configuration fields
    uses_mcp: bool = Field(default=True, exclude=True)
    mcp_server_name: str = Field(..., exclude=True)
    mcp_tool_name: str = Field(..., exclude=True)
    mcp_server_definition: MCPServerDefinition = Field(..., exclude=True)
    
    def get_mcp_config(self) -> Dict[str, any]:
        """
        Get MCP configuration for this tool.
        
        Returns:
            Dictionary containing MCP server details and tool configuration.
        """
        return {
            "server_name": self.mcp_server_name,
            "tool_name": self.mcp_tool_name,
            "server_definition": self.mcp_server_definition,
        }
    
    def execute(self, **kwargs) -> str:
        """
        MCP tools don't execute locally - they're executed via MCPExecutionActivity.
        
        This method should not be called directly for MCP tools. Instead, the
        workflow routes MCP tools to the MCPExecutionActivity for remote execution.
        
        Raises:
            RuntimeError: Always, as MCP tools should be executed via activity.
        """
        raise RuntimeError(
            f"MCP tool '{self.NAME}' should be executed via MCPExecutionActivity, "
            "not called directly."
        )