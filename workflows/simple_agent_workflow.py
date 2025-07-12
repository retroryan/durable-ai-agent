"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from models.types import Response


@workflow.defn
class SimpleAgentWorkflow:
    """A simple workflow that calls find_events activity."""

    def __init__(self):
        """Initialize workflow state."""
        self.query_count = 0

    @workflow.run
    async def run(self, user_message: str, user_name: str = "anonymous") -> Response:
        """
        Main workflow execution.

        Args:
            user_message: The message from the user
            user_name: The name of the user

        Returns:
            Response with event information
        """
        # Increment query counter to demonstrate state persistence
        self.query_count += 1

        # Route to appropriate activity based on user message content
        if "weather" in user_message.lower():
            activity_result = await workflow.execute_activity(
                "weather_forecast_activity",
                args=[user_message, user_name],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                ),
            )
        else:
            # Default to events activity (backward compatibility)
            activity_result = await workflow.execute_activity(
                "find_events_activity",
                args=[user_message, user_name],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                ),
            )

        # Return structured response
        # Handle different activity response formats
        return Response(
            message=activity_result["message"],
            event_count=activity_result.get("event_count", 0),  # Default to 0 for non-event activities
            query_count=self.query_count,
        )

    @workflow.query
    def get_query_count(self) -> int:
        """Query handler to expose workflow state."""
        return self.query_count

    @workflow.query
    def get_status(self) -> str:
        """Query handler to get workflow status."""
        return f"Workflow has processed {self.query_count} queries"
