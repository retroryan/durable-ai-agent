"""Activity for executing a tool from a tool registry."""
import logging
import time
from typing import Any, Dict, List, Optional

from temporalio import activity

from models.trajectory import Trajectory
from models.types import ActivityStatus, MCPConfig, ToolExecutionRequest, ToolExecutionResult
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

    def _update_trajectory_observation(self, trajectories: List[Trajectory], observation: str) -> None:
        """Update the latest trajectory with an observation."""
        if trajectories:
            trajectories[-1].observation = observation

    def _create_error_result(
        self, 
        error_message: str, 
        trajectories: List[Trajectory],
        execution_time: float = 0.0
    ) -> ToolExecutionResult:
        """Create an error result and update trajectory."""
        self._update_trajectory_observation(trajectories, f"Error: {error_message}")
        return ToolExecutionResult(
            success=False,
            error=error_message,
            trajectories=trajectories,
            execution_time=execution_time
        )

    async def _execute_mcp_tool(
        self,
        tool: Any,
        tool_name: str,
        tool_args: Dict[str, Any],
        logger: logging.Logger
    ) -> str:
        """Execute an MCP tool and return the observation."""
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
        return observation

    def _execute_traditional_tool(
        self,
        tool: Any,
        tool_name: str,
        tool_args: Dict[str, Any],
        logger: logging.Logger
    ) -> str:
        """Execute a traditional tool and return the observation."""
        logger.debug(f"Executing traditional tool: {tool_name}")
        result = tool.execute(**tool_args)
        logger.debug(f"Tool result: {result}")
        return str(result)

    @activity.defn
    async def execute_tool(
        self,
        request: ToolExecutionRequest,
    ) -> ToolExecutionResult:
        """
        Activity that executes a specified tool and updates the trajectory.

        Args:
            request: ToolExecutionRequest containing tool_name, tool_args, trajectory, and current_iteration.

        Returns:
            ToolExecutionResult with execution status and updated trajectories.
        """
        logger = activity.logger
        start_time = time.time()
        
        # Extract values from request
        tool_name = request.tool_name
        tool_args = request.tool_args
        trajectories = request.trajectories

        # Validate tool registry
        if not self.tool_registry:
            logger.error("ToolExecutionActivity not properly initialized with tool_registry")
            return self._create_error_result(
                "Tool registry not initialized",
                trajectories
            )

        # Check if tool exists
        if tool_name not in self.tool_registry.get_all_tools():
            logger.warning(f"Unknown tool: {tool_name}")
            return self._create_error_result(
                f"Unknown tool {tool_name}",
                trajectories
            )

        # Execute the tool
        try:
            tool = self.tool_registry.get_tool(tool_name)
            tool_class = tool.__class__
            
            # Check if this is an MCP tool
            if getattr(tool_class, 'is_mcp', False):
                observation = await self._execute_mcp_tool(tool, tool_name, tool_args, logger)
            else:
                observation = self._execute_traditional_tool(tool, tool_name, tool_args, logger)
            
            # Update trajectory with successful observation
            self._update_trajectory_observation(trajectories, observation)
            
            execution_time = time.time() - start_time
            return ToolExecutionResult(
                success=True,
                trajectories=trajectories,
                execution_time=execution_time,
                error=None
            )

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            execution_time = time.time() - start_time
            return self._create_error_result(
                str(e),
                trajectories,
                execution_time
            )
    
    async def cleanup(self):
        """Clean up MCP connections"""
        await self.mcp_client_manager.cleanup()
