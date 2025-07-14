"""Activity that integrates ExtractAgent with Temporal workflows."""
from typing import Any, Dict

from temporalio import activity

from models.types import ExtractAgentActivityResult


class ExtractAgentActivity:
    """An Extract agent activity that uses a pre-initialized agent."""

    def __init__(self, extract_agent):
        """
        Initialize with a pre-configured ReactExtract agent.

        Args:
            extract_agent: The initialized agent from agentic_loop
        """
        self._extract_agent = extract_agent

    @activity.defn
    async def run_extract_agent(
        self, trajectory: Dict[str, Any], user_query: str, user_name: str = "anonymous"
    ) -> ExtractAgentActivityResult:
        """
        Activity that runs the ExtractAgent to synthesize a final answer from trajectory.

        Args:
            trajectory: The complete agent execution trajectory
            user_query: The original user's query
            user_name: The name of the user making the request

        Returns:
            ExtractAgentActivityResult with status, answer, reasoning, and optional error
        """
        # Get activity info for context
        info = activity.info()
        workflow_id = info.workflow_id
        activity_id = info.activity_id

        # Log the activity execution with user context
        activity.logger.info(
            f"[ExtractAgentActivity Activity] Starting execution - Activity ID: {activity_id}, "
            f"Workflow ID: {workflow_id}, User: '{user_name}'"
        )
        activity.logger.info(
            f"[ExtractAgentActivity Activity] User query: '{user_query}'"
        )
        activity.logger.debug(
            f"[ExtractAgentActivity Activity] Full activity info - Task: {info.task_token}, "
            f"Attempt: {info.attempt}"
        )

        try:
            activity.logger.info(
                f"[ExtractAgentActivity Activity] Extracting final answer from trajectory"
            )

            # Run the extract agent to synthesize the final answer
            extract_result = self._extract_agent(
                trajectory=trajectory, user_query=user_query
            )

            # Extract the answer and reasoning from the prediction
            answer = getattr(extract_result, "answer", None)
            reasoning = getattr(extract_result, "reasoning", None)

            activity.logger.info(
                f"[ExtractAgentActivity Activity] Extract completed - Answer: {answer}"
            )
            activity.logger.debug(
                f"[ExtractAgentActivity Activity] Full extract result: {extract_result}"
            )

            return ExtractAgentActivityResult(
                status="success",
                answer=answer,
                reasoning=reasoning,
                trajectory=trajectory,
            )

        except Exception as e:
            activity.logger.error(
                f"[ExtractAgentActivity Activity] Error during execution: {str(e)}"
            )
            activity.logger.exception(
                f"[ExtractAgentActivity Activity] Full exception details:"
            )

            # Extract display name for error message too
            display_name = (
                user_name.split("_")[0] + "_" + user_name.split("_")[1]
                if "_" in user_name
                else user_name
            )

            activity.logger.error(
                f"[ExtractAgentActivity Activity] Returning error result for user '{display_name}'"
            )

            return ExtractAgentActivityResult(
                status="error",
                trajectory=trajectory,
                error=str(e),
            )