"""Activity that integrates ReactAgent with Temporal workflows."""
from typing import Any, Dict, Tuple

from temporalio import activity

from models.types import ActivityStatus, ReactAgentActivityResult


class ReactAgentActivity:
    """A ReAct agent activity that uses a pre-initialized agent."""

    def __init__(self, react_agent):
        """
        Initialize with a pre-configured ReactAgent.

        Args:
            react_agent: The initialized agent from agentic_loop
        """
        self._react_agent = react_agent

    @activity.defn
    async def run_react_agent(
        self, 
        user_query: str, 
        current_iteration: int, 
        trajectory: Dict[str, Any],
        user_name: str = "anonymous"
    ) -> ReactAgentActivityResult:
        """
        Activity that runs the ReactAgent for one iteration.

        Args:
            user_query: The user's query
            current_iteration: The current iteration number
            trajectory: The accumulated trajectory from previous iterations
            user_name: The name of the user making the request

        Returns:
            ReactAgentActivityResult with status, trajectory, tool_name, and optional error
        """
        # Get activity info for context
        info = activity.info()
        workflow_id = info.workflow_id
        activity_id = info.activity_id

        # Log the activity execution with user context
        activity.logger.info(
            f"[ReactAgentActivity Activity] Starting execution - Activity ID: {activity_id}, "
            f"Workflow ID: {workflow_id}, User: '{user_name}'"
        )
        activity.logger.info(
            f"[ReactAgentActivity Activity] User query: '{user_query}'"
        )
        activity.logger.debug(
            f"[ReactAgentActivity Activity] Full activity info - Task: {info.task_token}, "
            f"Attempt: {info.attempt}"
        )

        try:
            activity.logger.info(
                f"[ReactAgentActivity Activity] Executing React iteration for query: '{user_query}'"
            )

            # Run the react agent for one iteration
            trajectory, tool_name, tool_args = self._execute_react_iteration(
                user_query, current_iteration, trajectory
            )

            activity.logger.info(
                f"[ReactAgentActivity Activity] React iteration completed - Trajectory: {trajectory}, "
                f"Tool Name: {tool_name}"
            )
            activity.logger.debug(
                f"[ReactAgentActivity Activity] Full trajectory: {trajectory}"
            )

            return ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectory=trajectory,
                tool_name=tool_name,
                tool_args=tool_args,
            )

        except Exception as e:
            activity.logger.error(
                f"[ReactAgentActivity Activity] Error during execution: {str(e)}"
            )
            activity.logger.exception(
                f"[ReactAgentActivity Activity] Full exception details:"
            )

            # Extract display name for error message too
            display_name = (
                user_name.split("_")[0] + "_" + user_name.split("_")[1]
                if "_" in user_name
                else user_name
            )

            activity.logger.error(
                f"[ReactAgentActivity Activity] Returning error result for user '{display_name}'"
            )

            return ReactAgentActivityResult(
                status=ActivityStatus.ERROR,
                trajectory={},
                tool_name="",
                user_name=display_name,
                error=str(e),
            )

    def _execute_react_iteration(
        self, user_query: str, current_iteration: int, trajectory: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str, Dict[str, Any]]:
        """
        Execute a single React agent iteration.

        Args:
            user_query: The user's question
            current_iteration: The current iteration number
            trajectory: The accumulated trajectory from previous iterations

        Returns:
            Tuple[Dict[str, Any], str, Dict[str, Any]]: (trajectory, tool_name, tool_args)
        """
        activity.logger.info(
            f"[ReactAgentActivity] _execute_react_iteration called with query: '{user_query}', "
            f"iteration: {current_iteration}, trajectory keys: {list(trajectory.keys())}"
        )
        activity.logger.info(
            f"[ReactAgentActivity] About to call self._react_agent - Type: {type(self._react_agent)}, "
            f"Iteration: {current_iteration}"
        )

        try:
            # Add logging before the actual call
            activity.logger.info(
                f"[ReactAgentActivity] Calling _react_agent with params - "
                f"trajectory: {trajectory}, iteration: {current_iteration}, query: '{user_query}'"
            )

            # Call ReactAgent for one iteration - returns the same types as forward method
            result = self._react_agent(
                trajectory=trajectory,
                current_iteration=current_iteration,
                user_query=user_query,
            )

            activity.logger.info(
                f"[ReactAgentActivity] _react_agent returned - Type: {type(result)}, "
                f"Length: {len(result) if isinstance(result, tuple) else 'N/A'}"
            )

            # Extract trajectory, tool_name and tool_args from ReactAgentResult
            trajectory = result.trajectory
            tool_name = result.tool_name
            tool_args = result.tool_args

            activity.logger.info(
                f"[ReactAgentActivity] Unpacked results - trajectory: {trajectory}, "
                f"Tool Name: {tool_name}, Tool Args: {tool_args}"
            )

        except Exception as e:
            activity.logger.error(
                f"[ReactAgentActivity] Error calling _react_agent: {type(e).__name__}: {str(e)}"
            )
            activity.logger.exception("[ReactAgentActivity] Full traceback:")
            raise

        activity.logger.info(
            f"[ReactAgentActivity] _execute_react_iteration completed successfully"
        )

        return trajectory, tool_name, tool_args
