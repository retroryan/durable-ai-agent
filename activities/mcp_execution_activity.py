"""Activity for executing MCP-based tools via MCP client."""
import logging
from typing import Any, Dict, Optional

from temporalio import activity

from models.types import ActivityStatus, ToolExecutionRequest
from shared.mcp_client_manager import MCPClientManager
from shared.tool_utils.mcp_tool import MCPTool
from shared.tool_utils.registry import ToolRegistry


class MCPExecutionActivity:
    """Activity for executing MCP-based tools."""
    
    def __init__(self, tool_registry: ToolRegistry = None):
        """
        Initialize with tool registry and MCP client manager.
        
        Args:
            tool_registry: Registry containing tool definitions including MCP tools
        """
        self.tool_registry = tool_registry
        self.mcp_client_manager = MCPClientManager()
    
    @activity.defn
    async def execute_mcp_tool(
        self,
        request: ToolExecutionRequest,
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool and update trajectory.
        
        Args:
            request: ToolExecutionRequest with tool_name, args, trajectory, iteration
            
        Returns:
            Dictionary with status and updated trajectory
        """
        logger = activity.logger
        
        # Extract request data
        tool_name = request.tool_name
        tool_args = request.tool_args
        trajectory = request.trajectory
        current_iteration = request.current_iteration
        
        # Validate tool registry
        if not self.tool_registry:
            logger.error(
                "MCPExecutionActivity not properly initialized with tool_registry"
            )
            trajectory[
                f"observation_{current_iteration-1}"
            ] = "Error: Tool registry not initialized."
            return {
                "status": ActivityStatus.ERROR,
                "error": "MCPExecutionActivity not properly initialized with tool_registry",
                "trajectory": trajectory,
            }
        
        try:
            # Get tool from registry
            tool = self.tool_registry.get_tool(tool_name)
            
            # Verify it's an MCP tool
            if not isinstance(tool, MCPTool):
                raise ValueError(f"Tool {tool_name} is not an MCP tool")
            
            # Get MCP configuration
            mcp_config = tool.get_mcp_config()
            
            # Get or create MCP client
            client = await self.mcp_client_manager.get_client(
                mcp_config["server_definition"]
            )
            
            # Call the MCP tool
            logger.info(f"Calling MCP tool: {mcp_config['tool_name']} with args: {tool_args}")
            result = await client.call_tool(
                name=mcp_config["tool_name"],
                arguments=tool_args
            )
            
            # Process result
            if hasattr(result, 'content'):
                # Handle structured responses
                observation = str(result.content[0].text if result.content else "No result")
            else:
                observation = str(result)
            
            logger.debug(f"MCP tool result: {observation}")
            
            # Update trajectory
            idx = current_iteration - 1
            trajectory[f"observation_{idx}"] = observation
            
            return {
                "status": ActivityStatus.SUCCESS,
                "trajectory": trajectory,
            }
            
        except Exception as e:
            logger.error(f"MCP tool execution error: {e}", exc_info=True)
            trajectory[f"observation_{current_iteration-1}"] = f"Error: {str(e)}"
            return {
                "status": ActivityStatus.ERROR,
                "error": str(e),
                "trajectory": trajectory,
            }
    
    async def cleanup(self):
        """Clean up MCP connections"""
        await self.mcp_client_manager.cleanup()