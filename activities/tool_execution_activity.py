"""Activity for executing a tool from a tool registry."""
import logging
from typing import Any, Dict

from temporalio import activity

from models.types import ActivityStatus, MCPConfig, ToolExecutionRequest
from shared.mcp_client_manager import MCPClientManager
from shared.tool_utils.mcp_tool import MCPTool
from shared.tool_utils.registry import ToolRegistry


class ToolExecutionActivity:
    """An activity for executing tools from a tool registry."""

    def __init__(self, tool_registry: ToolRegistry = None):
        """
        Initializes the ToolExecutionActivity with a tool registry.

        Args:
            tool_registry: An instance of ToolRegistry containing available tools.
        """
        self.tool_registry = tool_registry
        self.mcp_client_manager = MCPClientManager()  # Lightweight, always create

    @activity.defn
    async def execute_tool(
        self,
        request: ToolExecutionRequest,
    ) -> Dict[str, Any]:
        """
        Activity that executes a specified tool and updates the trajectory.

        Args:
            request: ToolExecutionRequest containing tool_name, tool_args, trajectory, and current_iteration.

        Returns:
            A dictionary containing the status and the updated trajectory.
        """
        logger = activity.logger
        
        # Extract values from request
        tool_name = request.tool_name
        tool_args = request.tool_args
        trajectory = request.trajectory
        current_iteration = request.current_iteration

        if not self.tool_registry:
            logger.error(
                "ToolExecutionActivity not properly initialized with tool_registry"
            )
            trajectory[
                f"observation_{current_iteration-1}"
            ] = "Error: Tool registry not initialized."
            return {
                "status": ActivityStatus.ERROR,
                "error": "ToolExecutionActivity not properly initialized with tool_registry",
                "trajectory": trajectory,
            }

        tool_registry = self.tool_registry

        if tool_name in tool_registry.get_all_tools():
            try:
                tool = tool_registry.get_tool(tool_name)
                tool_class = tool.__class__
                
                # Check if this is an MCP tool using the class variable
                if getattr(tool_class, 'is_mcp', False):
                    # Execute as MCP tool
                    logger.debug(f"Executing MCP tool: {tool_name}")
                    
                    # Get MCP configuration
                    mcp_config = tool.get_mcp_config()
                    
                    # Get or create MCP client
                    client = await self.mcp_client_manager.get_client(
                        mcp_config.server_definition
                    )
                    
                    # Call the MCP tool - wrap args in 'request' for proxy compatibility
                    logger.info(f"Calling MCP tool: {mcp_config.tool_name} with args: {tool_args}")
                    wrapped_args = {"request": tool_args}
                    result = await client.call_tool(
                        name=mcp_config.tool_name,
                        arguments=wrapped_args
                    )
                    
                    # Process MCP result
                    if hasattr(result, 'content'):
                        # Handle structured responses
                        observation = str(result.content[0].text if result.content else "No result")
                    else:
                        observation = str(result)
                    
                    logger.debug(f"MCP tool result: {observation}")
                    
                    # Update trajectory
                    idx = current_iteration - 1
                    trajectory[f"observation_{idx}"] = observation
                else:
                    # Execute as traditional tool
                    logger.debug(f"Executing traditional tool: {tool_name}")
                    result = tool.execute(**tool_args)
                    logger.debug(f"Tool result: {result}")

                    # Add tool result to trajectory
                    idx = current_iteration - 1
                    trajectory[f"observation_{idx}"] = result

            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                trajectory[f"observation_{current_iteration-1}"] = f"Error: {e}"
        else:
            logger.warning(f"Unknown tool: {tool_name}")
            trajectory[
                f"observation_{current_iteration-1}"
            ] = f"Error: Unknown tool {tool_name}"

        return {
            "status": ActivityStatus.SUCCESS,
            "trajectory": trajectory,
        }
    
    async def cleanup(self):
        """Clean up MCP connections"""
        await self.mcp_client_manager.cleanup()
