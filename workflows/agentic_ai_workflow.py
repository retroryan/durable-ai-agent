"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from activities.tool_execution_activity import ToolExecutionActivity
from models.types import ReactAgentActivityResult, Response, ToolExecutionRequest

with workflow.unsafe.imports_passed_through():
    from activities.react_agent_activity import ReactAgentActivity


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
        # Log workflow start
        workflow.logger.info(
            f"[AgenticAIWorkflow] Starting workflow execution for user: {user_name}, "
            f"workflow_id: {workflow.info().workflow_id}, "
            f"parent_workflow_id: {workflow.info().parent.workflow_id if workflow.info().parent else 'None'}"
        )
        workflow.logger.info(f"[AgenticAIWorkflow] User message: '{user_message}'")

        # Increment query counter to demonstrate state persistence
        self.query_count += 1
        workflow.logger.info(f"[AgenticAIWorkflow] Query count: {self.query_count}")

        # Call the ReactAgentActivity activity using the method pattern
        workflow.logger.info(
            f"[AgenticAIWorkflow] Calling ReactAgentActivity activity for message: '{user_message}'"
        )

        try:
            agent_result = await workflow.execute_activity_method(
                ReactAgentActivity.run_react_agent,
                args=[user_message, user_name],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )

            workflow.logger.info(
                f"[AgenticAIWorkflow] ReactAgentActivity activity completed successfully. "
                f"Status: {agent_result.status}"
            )
            workflow.logger.debug(
                f"[AgenticAIWorkflow] Full agent result: {agent_result}"
            )

        except Exception as e:
            workflow.logger.error(
                f"[AgenticAIWorkflow] Error calling ReactAgentActivity activity: {e}"
            )
            raise

        # Print out the tool calls that need to be made
        if agent_result.status == "success":
            tool_name = agent_result.tool_name
            tool_args = agent_result.tool_args or {}
            trajectory = agent_result.trajectory

            workflow.logger.info(
                f"[AgenticAIWorkflow] Agent decision - Tool: {tool_name}, Args: {tool_args}"
            )

            # Create message showing the tool call decision
            if tool_name == "finish":
                tool_call_info = "Agent decided to finish the task"
            else:
                # Create ToolExecutionRequest as soon as we get the results
                tool_request = ToolExecutionRequest(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    trajectory=trajectory,
                    current_iteration=1  # This should be extracted from trajectory if needed
                )
                tool_result, tool_call_info = await self.execute_tool(tool_request)

            response_message = f"Query processed for {agent_result.user_name or user_name}. {tool_call_info}"

            # Log the trajectory for debugging
            workflow.logger.info(f"[AgenticAIWorkflow] Agent trajectory: {trajectory}")
            workflow.logger.info(
                f"[AgenticAIWorkflow] Tool call decision: {tool_call_info}"
            )

        else:
            response_message = f"Agent error for {agent_result.user_name or user_name}: {agent_result.error or 'Unknown error'}"
            workflow.logger.error(
                f"[AgenticAIWorkflow] ReactAgentActivity failed with status: {agent_result.status}, "
                f"error: {agent_result.error or 'Unknown error'}"
            )
            workflow.logger.debug(
                f"[AgenticAIWorkflow] Full error result: {agent_result}"
            )

        # Return structured response
        workflow.logger.info(
            f"[AgenticAIWorkflow] Workflow completed. Response message: '{response_message}'"
        )

        return Response(
            message=response_message,
            event_count=0,  # No events executed, just tool planning
            query_count=self.query_count,
        )

    async def execute_tool(self, request: ToolExecutionRequest):
        tool_call_info = (
            f"Agent wants to call tool: {request.tool_name} with args: {request.tool_args}"
        )
        
        tool_result = await workflow.execute_activity_method(
            ToolExecutionActivity.execute_tool,
            args=[request],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                maximum_attempts=3,
            ),
        )
        return tool_result, tool_call_info

    @workflow.query
    def get_query_count(self) -> int:
        """Query handler to expose workflow state."""
        return self.query_count

    @workflow.query
    def get_status(self) -> str:
        """Query handler to get workflow status."""
        return f"Workflow has processed {self.query_count} queries"
