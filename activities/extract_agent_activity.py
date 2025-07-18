"""Activity that integrates ExtractAgent with Temporal workflows."""
from typing import Any, Dict

import dspy
from temporalio import activity

from models.types import ActivityStatus, ExtractAgentActivityResult


# Create a signature for answer extraction
class AnswerExtractionSignature(dspy.Signature):
    """Extract a clear, concise answer from the gathered information."""

    user_query: str = dspy.InputField(desc="The user's original question")
    answer: str = dspy.OutputField(
        desc="Clear, direct answer to the user's question"
    )


class ExtractAgentActivity:
    """An Extract agent activity that creates its own ReactExtract agent."""

    def __init__(self):
        """
        Initialize the activity. Creates its own ReactExtract with AnswerExtractionSignature.
        """
        # Import here to avoid circular imports
        from agentic_loop.extract_agent import ReactExtract
        
        # Create our own ReactExtract with the AnswerExtractionSignature
        self._extract_agent = ReactExtract(signature=AnswerExtractionSignature)

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
            # Following the exact pattern from demo_react_agent.extract_final_answer
            extract_result = self._extract_agent(
                trajectory=trajectory, user_query=user_query
            )

            # Extract the answer from the result (reasoning is not in our signature)
            answer = extract_result.answer
            reasoning = getattr(extract_result, "reasoning", "")

            activity.logger.info(
                f"[ExtractAgentActivity Activity] Extract completed - Answer: {answer}"
            )
            activity.logger.debug(
                f"[ExtractAgentActivity Activity] Full extract result: {extract_result}"
            )

            return ExtractAgentActivityResult(
                status=ActivityStatus.SUCCESS,
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
                status=ActivityStatus.ERROR,
                trajectory=trajectory,
                error=str(e),
            )