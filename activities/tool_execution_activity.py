"""Activity for executing a tool from a tool registry."""
import logging
from typing import Any, Dict

from temporalio import activity

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

    @activity.defn
    async def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        trajectory: Dict[str, Any],
        current_iteration: int,
    ) -> Dict[str, Any]:
        """
        Activity that executes a specified tool and updates the trajectory.

        Args:
            tool_name: The name of the tool to execute.
            tool_args: The arguments for the tool.
            trajectory: The current state of the agent's trajectory.
            current_iteration: The current iteration number.

        Returns:
            A dictionary containing the status and the updated trajectory.
        """
        logger = activity.logger

        if not self.tool_registry:
            logger.error(
                "ToolExecutionActivity not properly initialized with tool_registry"
            )
            trajectory[
                f"observation_{current_iteration-1}"
            ] = "Error: Tool registry not initialized."
            return {
                "status": "error",
                "error": "ToolExecutionActivity not properly initialized with tool_registry",
                "trajectory": trajectory,
            }

        tool_registry = self.tool_registry

        if tool_name in tool_registry.get_all_tools():
            try:
                tool = tool_registry.get_tool(tool_name)
                logger.debug(f"Executing tool: {tool_name}")
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
            "status": "success",
            "trajectory": trajectory,
        }
