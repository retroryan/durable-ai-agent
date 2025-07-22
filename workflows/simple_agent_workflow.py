"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from workflows.agentic_ai_workflow import AgenticAIWorkflow
    from models.types import Response


@workflow.defn
class SimpleAgentWorkflow:
    """A simple workflow that calls find_events activity."""

    def __init__(self):
        """Initialize workflow state."""
        self.query_count = 0

    async def _handle_weather_query(self, prompt: str, user_name: str) -> dict:
        """Handle weather queries that start with 'weather:' prefix."""
        # Extract the query after "weather:"
        query = prompt[8:].strip()  # Remove "weather:" prefix and trim whitespace
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Weather prefix detected, extracted query: '{query}'"
        )
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Executing child workflow AgenticAIWorkflow for user '{user_name}'"
        )

        # Execute the child workflow for weather queries
        child_workflow_id = f"agentic-ai-weather-{workflow.info().workflow_id}"
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Child workflow ID: {child_workflow_id}"
        )

        try:
            child_result = await workflow.execute_child_workflow(
                AgenticAIWorkflow,
                args=[
                    query,
                    user_name,
                ],
                id=child_workflow_id,
            )

            workflow.logger.info(
                f"[SimpleAgentWorkflow] Child workflow completed successfully"
            )
            workflow.logger.debug(
                f"[SimpleAgentWorkflow] Child workflow result: {child_result}"
            )

        except Exception as e:
            workflow.logger.error(
                f"[SimpleAgentWorkflow] Error executing child workflow: {e}"
            )
            raise

        # Convert child workflow result to expected format
        activity_result = {
            "message": child_result.message,
            "event_count": child_result.event_count,
        }
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Converted child workflow result to activity format"
        )
        return activity_result


    async def _handle_default_query(self, prompt: str, user_name: str) -> dict:
        """Handle default queries (backward compatibility with events)."""
        workflow.logger.info(
            f"[SimpleAgentWorkflow] No specific keyword detected, defaulting to find_events_activity"
        )
        return await workflow.execute_activity(
            "find_events_activity",
            args=[prompt, user_name],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

    @workflow.run
    async def run(self, prompt: str, user_name: str = "anonymous") -> Response:
        """
        Main workflow execution.

        Args:
            prompt: The message from the user
            user_name: The name of the user

        Returns:
            Response with event information
        """
        # Log workflow start
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Starting workflow execution - "
            f"Workflow ID: {workflow.info().workflow_id}, User: {user_name}"
        )
        workflow.logger.info(f"[SimpleAgentWorkflow] User message: '{prompt}'")

        # Increment query counter to demonstrate state persistence
        self.query_count += 1
        workflow.logger.info(f"[SimpleAgentWorkflow] Query count: {self.query_count}")

        # Route to appropriate activity based on user message content
        if prompt.lower().startswith("weather:"):
            activity_result = await self._handle_weather_query(prompt, user_name)
        else:
            activity_result = await self._handle_default_query(prompt, user_name)

        # Return structured response
        # Handle different activity response formats
        response = Response(
            message=activity_result["message"],
            event_count=activity_result.get(
                "event_count", 0
            ),  # Default to 0 for non-event activities
            query_count=self.query_count,
        )

        workflow.logger.info(
            f"[SimpleAgentWorkflow] Workflow completed successfully. "
            f"Response message: '{response.message}', Event count: {response.event_count}"
        )

        return response

    @workflow.query
    def get_query_count(self) -> int:
        """Query handler to expose workflow state."""
        return self.query_count

    @workflow.query
    def get_status(self) -> str:
        """Query handler to get workflow status."""
        return f"Workflow has processed {self.query_count} queries"
