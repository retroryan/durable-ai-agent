"""Activity that integrates ReactAgent with Temporal workflows."""
import logging
from typing import Any, Dict, Tuple

from temporalio import activity


class ReactAgent:
    """A ReAct agent activity that uses a pre-initialized agent."""

    def __init__(self, agentic_react_agent):
        """
        Initialize with a pre-configured AgenticReactAgent.

        Args:
            agentic_react_agent: The initialized agent from agentic_loop
        """
        self._react_agent = agentic_react_agent

    @activity.defn
    async def run_react_agent(
        self, user_query: str, user_name: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        Activity that runs the ReactAgent for one iteration.

        Args:
            user_query: The user's query
            user_name: The name of the user making the request

        Returns:
            Dictionary with trajectory, tool_name, tool_args, and execution status
        """
        # Get activity info for context
        info = activity.info()
        workflow_id = info.workflow_id

        # Log the activity execution with user context
        activity.logger.info(
            f"User '{user_name}' (workflow: {workflow_id}) running ReactAgent with query: {user_query}"
        )

        try:
            # Run the react agent for one iteration
            trajectory, tool_name, tool_args = self._execute_react_iteration(user_query)

            # Extract display name for response
            display_name = (
                user_name.split("_")[0] + "_" + user_name.split("_")[1]
                if "_" in user_name
                else user_name
            )

            return {
                "status": "success",
                "trajectory": trajectory,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "user_name": display_name,
            }

        except Exception as e:
            activity.logger.error(f"Error running ReactAgent: {e}")
            # Extract display name for error message too
            display_name = (
                user_name.split("_")[0] + "_" + user_name.split("_")[1]
                if "_" in user_name
                else user_name
            )
            return {
                "status": "error",
                "error": str(e),
                "user_name": display_name,
            }

    def _execute_react_iteration(
        self, user_query: str
    ) -> Tuple[Dict[str, Any], str, Dict[str, Any]]:
        """
        Execute a single React agent iteration.

        Args:
            user_query: The user's question

        Returns:
            Tuple[Dict[str, Any], str, Dict[str, Any]]: (trajectory, tool_name, tool_args)
        """
        trajectory: Dict[str, Any] = {}
        current_iteration = 1

        # Call ReactAgent for one iteration - returns the same types as forward method
        trajectory, tool_name, tool_args = self._react_agent(
            trajectory=trajectory,
            current_iteration=current_iteration,
            user_query=user_query,
        )

        return trajectory, tool_name, tool_args
