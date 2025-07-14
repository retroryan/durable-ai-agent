"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from activities.react_agent_activity import ReactAgent
from models.types import Response


@workflow.defn
class AgenticAIWorkflow:
    """An agentic ai workflow that calls find_events activity."""

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

        # Call the ReactAgent activity using the method pattern
        agent_result = await workflow.execute_activity_method(
            ReactAgent.run_react_agent,
            args=[user_message, user_name],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                maximum_attempts=3,
            ),
        )

        # Print out the tool calls that need to be made
        if agent_result["status"] == "success":
            tool_name = agent_result["tool_name"]
            tool_args = agent_result.get("tool_args", {})
            trajectory = agent_result.get("trajectory", {})

            # Create message showing the tool call decision
            if tool_name == "finish":
                tool_call_info = "Agent decided to finish the task"
            else:
                tool_call_info = (
                    f"Agent wants to call tool: {tool_name} with args: {tool_args}"
                )

            response_message = (
                f"Query processed for {agent_result['user_name']}. {tool_call_info}"
            )

            # Log the trajectory for debugging
            workflow.logger.info(f"Agent trajectory: {trajectory}")
            workflow.logger.info(f"Tool call decision: {tool_call_info}")

        else:
            response_message = f"Agent error for {agent_result['user_name']}: {agent_result.get('error', 'Unknown error')}"
            workflow.logger.error(f"ReactAgent failed: {agent_result}")

        # Return structured response
        return Response(
            message=response_message,
            event_count=0,  # No events executed, just tool planning
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
