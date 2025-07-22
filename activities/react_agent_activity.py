"""Activity that integrates ReactAgent with Temporal workflows."""
from typing import Any, Dict, List, Tuple

from temporalio import activity

from models.trajectory import Trajectory
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
        prompt: str,
        current_iteration: int, 
        trajectories: List[Trajectory],
        user_name: str = "anonymous"
    ) -> ReactAgentActivityResult:
        """
        Activity that runs the ReactAgent for one iteration.

        Args:
            prompt: The user's prompt
            current_iteration: The current iteration number
            trajectories: The list of trajectory steps from previous iterations
            user_name: The name of the user making the request

        Returns:
            ReactAgentActivityResult with status, trajectories, current_trajectory, and optional error
        """
        # Get activity info for context
        info = activity.info()
        workflow_id = info.workflow_id
        activity_id = info.activity_id

        # Log the activity execution with user context
        activity.logger.info(
            f"[ReactAgentActivity Activity] Starting execution - Activity ID: {activity_id}, "
            f"Workflow ID: {workflow_id}, User: '{user_name}' Prompt: '{prompt}'"
        )
        try:
            activity.logger.info(
                f"[ReactAgentActivity Activity] Executing React iteration for prompt: '{prompt}'"
            )

            # Run the react agent for one iteration
            current_trajectory = self._execute_react_iteration(
                prompt, current_iteration, trajectories
            )
            
            # Add the new trajectory to the list
            trajectories.append(current_trajectory)

            activity.logger.info(
                f"[ReactAgentActivity Activity] React iteration completed - "
                f"Tool Name: {current_trajectory.tool_name}   -   "
                f"Current trajectory: {current_trajectory}"
            )

            return ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectories=trajectories,
            )

        except Exception as e:
            activity.logger.error(
                f"[ReactAgentActivity Activity] Error during execution: {str(e)}"
            )
            # Create an error trajectory
            error_trajectory = Trajectory(
                iteration=current_iteration - 1,
                thought="Error occurred during React agent execution",
                tool_name="error",
                tool_args={},
                error=str(e)
            )
            
            return ReactAgentActivityResult(
                status=ActivityStatus.ERROR,
                trajectories=trajectories + [error_trajectory],
                user_name=user_name,
                error=str(e),
            )

    def _execute_react_iteration(
        self, prompt: str, current_iteration: int, trajectories: List[Trajectory]
    ) -> Trajectory:
        """
        Execute a single React agent iteration.

        Args:
            prompt: The user's prompt
            current_iteration: The current iteration number
            trajectories: The list of trajectory steps from previous iterations

        Returns:
            Trajectory: The trajectory for this iteration
        """
        activity.logger.info(
            f"[ReactAgentActivity] _execute_react_iteration called with query: '{prompt}', "
            f"iteration: {current_iteration}, trajectories count: {len(trajectories)}"
        )

        try:
            # Add logging before the actual call
            activity.logger.info(
                f"[ReactAgentActivity] Calling _react_agent with params - "
                f"trajectories count: {len(trajectories)}, iteration: {current_iteration}, query: '{prompt}'"
            )

            # Call ReactAgent for one iteration - returns a Trajectory
            trajectory = self._react_agent(
                trajectories=trajectories,
                current_iteration=current_iteration,
                user_query=prompt,
            )

            activity.logger.info(
                f"[ReactAgentActivity] _react_agent returned Trajectory - "
                f"Tool: {trajectory.tool_name}, Iteration: {trajectory.iteration}"
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

        return trajectory
