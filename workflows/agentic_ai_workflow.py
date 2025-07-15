"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from datetime import timedelta
from typing import Any, Dict, List, Tuple

from temporalio import workflow
from temporalio.common import RetryPolicy

from models.types import (
    ActivityStatus,
    ExtractAgentActivityResult,
    ReactAgentActivityResult,
    Response,
    ToolExecutionRequest,
    ToolExecutionResult,
    WorkflowStatus,
)

with workflow.unsafe.imports_passed_through():
    import http.client
    import dspy
    import requests
    import urllib3
    from activities.extract_agent_activity import ExtractAgentActivity
    from activities.mcp_execution_activity import MCPExecutionActivity
    from activities.react_agent_activity import ReactAgentActivity
    from activities.tool_execution_activity import ToolExecutionActivity


@workflow.defn
class AgenticAIWorkflow:
    """An agentic ai workflow that calls find_events activity."""

    def __init__(self):
        """Initialize workflow state."""
        self.query_count = 0
        self.trajectory = {}
        self.tools_used = []
        self.current_iteration = 0
        self.execution_time = 0.0
        self.workflow_status = WorkflowStatus.INITIALIZED

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

        # Run the React agent loop
        self.workflow_status = WorkflowStatus.RUNNING_REACT_LOOP
        trajectory, tools_used, execution_time = await self._run_react_loop(
            user_message=user_message,
            user_name=user_name,
            max_iterations=5
        )
        
        # Update instance variables for state persistence
        self.trajectory = trajectory
        self.tools_used = tools_used
        self.execution_time = execution_time

        # Extract final answer using ExtractAgentActivity
        self.workflow_status = WorkflowStatus.EXTRACTING_ANSWER
        final_answer = await self._extract_final_answer(
            trajectory=trajectory,
            user_query=user_message,
            user_name=user_name
        )

        # Create response message
        workflow.logger.debug(f"[AgenticAIWorkflow] ExtractAgent result - Status: {final_answer.status}, Answer: '{final_answer.answer}', Answer type: {type(final_answer.answer)}")
        
        if final_answer.status == ActivityStatus.SUCCESS and final_answer.answer is not None and str(final_answer.answer).strip():
            # Return the clean, direct answer from ExtractAgent
            response_message = final_answer.answer
            workflow.logger.info(
                f"[AgenticAIWorkflow] Successfully extracted answer for {user_name}: {final_answer.answer}"
            )
        elif final_answer.status == ActivityStatus.SUCCESS:
            # If extraction succeeded but no answer, return the latest meaningful tool result from trajectory
            latest_observation = None
            for key in sorted(trajectory.keys(), reverse=True):
                if key.startswith("observation_") and not trajectory[key].startswith("Error:") and trajectory[key] != "Completed.":
                    latest_observation = trajectory[key]
                    break
            
            if latest_observation:
                response_message = latest_observation
                workflow.logger.info(
                    f"[AgenticAIWorkflow] Using latest meaningful observation as answer for {user_name}"
                )
            else:
                response_message = "No result found"
                workflow.logger.warning(
                    f"[AgenticAIWorkflow] No meaningful observations found in trajectory for {user_name}"
                )
        else:
            response_message = f"Error: {final_answer.error or 'Unknown error'}"
            workflow.logger.error(
                f"[AgenticAIWorkflow] Failed to extract answer for {user_name}: {final_answer.error}"
            )

        # Log summary
        workflow.logger.info(
            f"[AgenticAIWorkflow] Workflow completed. Tools used: {', '.join(tools_used) if tools_used else 'None'}, "
            f"Execution time: {execution_time:.2f}s"
        )
        
        self.workflow_status = WorkflowStatus.COMPLETED

        return Response(
            message=response_message,
            event_count=len(tools_used),
            query_count=self.query_count,
        )

    async def _run_react_loop(
        self,
        user_message: str,
        user_name: str,
        max_iterations: int = 5
    ) -> Tuple[Dict[str, Any], List[str], float]:
        """
        Run the React agent loop until completion or max iterations.

        Args:
            user_message: The user's query
            user_name: The name of the user
            max_iterations: Maximum number of iterations

        Returns:
            Tuple of (trajectory dictionary, tools used list, execution time)
        """
        trajectory = {}
        tools_used = []
        current_iteration = 1
        start_time = workflow.now()

        workflow.logger.info(
            f"[AgenticAIWorkflow] Starting React agent loop, max iterations: {max_iterations}"
        )

        # Loop until we get "finish" or hit max iterations
        while current_iteration <= max_iterations:
            workflow.logger.info(
                f"[AgenticAIWorkflow] Iteration {current_iteration}/{max_iterations}"
            )

            # Call ReactAgent activity
            agent_result = await self._call_react_agent(
                user_message=user_message,
                user_name=user_name,
                trajectory=trajectory,
                current_iteration=current_iteration
            )

            if agent_result.status != ActivityStatus.SUCCESS:
                workflow.logger.error(
                    f"[AgenticAIWorkflow] ReactAgent failed: {agent_result.error}"
                )
                self.workflow_status = WorkflowStatus.FAILED
                break

            # Update trajectory from agent result
            trajectory = agent_result.trajectory
            tool_name = agent_result.tool_name
            tool_args = agent_result.tool_args or {}
            
            # Update instance variable for state persistence
            self.trajectory = trajectory
            self.current_iteration = current_iteration

            workflow.logger.info(
                f"[AgenticAIWorkflow] Agent decision - Tool: {tool_name}, Args: {tool_args}"
            )

            # Check if we're done
            if tool_name == "finish":
                workflow.logger.info("[AgenticAIWorkflow] Agent selected 'finish' - task complete")
                # Add final observation for finish to match demo behavior
                idx = current_iteration - 1
                trajectory[f"observation_{idx}"] = "Completed."
                break

            # Execute the tool
            tool_result = await self._execute_tool(
                tool_name=tool_name,
                tool_args=tool_args,
                trajectory=trajectory,
                current_iteration=current_iteration
            )

            # Update trajectory with the one returned by tool execution
            # The ToolExecutionActivity already added the observation
            if tool_result.trajectory:
                trajectory = tool_result.trajectory
            
            # Track tools used
            if tool_name and tool_name != "finish":
                tools_used.append(tool_name)

            current_iteration += 1

        if current_iteration > max_iterations:
            workflow.logger.warning(
                f"[AgenticAIWorkflow] Reached maximum iterations ({max_iterations})"
            )

        execution_time = (workflow.now() - start_time).total_seconds()
        return trajectory, tools_used, execution_time

    async def _call_react_agent(
        self,
        user_message: str,
        user_name: str,
        trajectory: Dict[str, Any],
        current_iteration: int
    ) -> ReactAgentActivityResult:
        """
        Call the ReactAgent activity with proper error handling.

        Args:
            user_message: The user's query
            user_name: The name of the user
            trajectory: Current trajectory state
            current_iteration: Current iteration number

        Returns:
            ReactAgentActivityResult
        """
        try:
            # Call the activity with all required parameters
            result = await workflow.execute_activity_method(
                ReactAgentActivity.run_react_agent,
                args=[user_message, current_iteration, trajectory, user_name],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )
            
            workflow.logger.debug(
                f"[AgenticAIWorkflow] ReactAgent returned trajectory with keys: {list(result.trajectory.keys())}"
            )
            
            return result
        except Exception as e:
            workflow.logger.error(
                f"[AgenticAIWorkflow] Error calling ReactAgent activity: {e}"
            )
            raise

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        trajectory: Dict[str, Any],
        current_iteration: int
    ) -> ToolExecutionResult:
        """
        Execute a tool using the appropriate execution activity.
        
        For MCP tools (tools ending with '_mcp'), routes to MCPExecutionActivity.
        For other tools, routes to ToolExecutionActivity.

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            trajectory: Current trajectory state
            current_iteration: Current iteration number

        Returns:
            ToolExecutionResult
        """
        workflow.logger.info(
            f"[AgenticAIWorkflow] Executing tool: {tool_name} with args: {tool_args}"
        )

        tool_request = ToolExecutionRequest(
            tool_name=tool_name,
            tool_args=tool_args,
            trajectory=trajectory,
            current_iteration=current_iteration
        )

        try:
            # Check if this is an MCP tool by naming convention
            # MCP tools should end with '_mcp' suffix
            if tool_name.endswith('_mcp'):
                workflow.logger.info(f"[AgenticAIWorkflow] Routing to MCPExecutionActivity for tool: {tool_name}")
                # Execute via MCP activity
                result_dict = await workflow.execute_activity_method(
                    MCPExecutionActivity.execute_mcp_tool,
                    args=[tool_request],
                    start_to_close_timeout=timedelta(seconds=300),  # Longer timeout for network calls
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=10),
                        maximum_attempts=3,
                    ),
                )
            else:
                # Execute via regular tool activity
                result_dict = await workflow.execute_activity_method(
                    ToolExecutionActivity.execute_tool,
                    args=[tool_request],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(seconds=10),
                        maximum_attempts=3,
                    ),
                )
            
            # Get the updated trajectory from the activity
            updated_trajectory = result_dict.get("trajectory", trajectory)
            
            # Convert dict to ToolExecutionResult
            if result_dict.get("status") == ActivityStatus.SUCCESS:
                # Extract the observation for this iteration
                idx = current_iteration - 1
                observation_key = f"observation_{idx}"
                result_text = updated_trajectory.get(observation_key, "No result")
                
                result = ToolExecutionResult(
                    tool_name=tool_name,
                    success=True,
                    result=result_text,
                    parameters=tool_args,
                    trajectory=updated_trajectory
                )
            else:
                result = ToolExecutionResult(
                    tool_name=tool_name,
                    success=False,
                    error=result_dict.get("error", "Unknown error"),
                    parameters=tool_args,
                    trajectory=trajectory
                )
            
            workflow.logger.info(
                f"[AgenticAIWorkflow] Tool execution completed: {'success' if result.success else 'failed'}"
            )
            return result
        except Exception as e:
            workflow.logger.error(
                f"[AgenticAIWorkflow] Tool execution error: {e}"
            )
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
                trajectory=trajectory
            )

    async def _extract_final_answer(
        self,
        trajectory: Dict[str, Any],
        user_query: str,
        user_name: str
    ) -> ExtractAgentActivityResult:
        """
        Extract the final answer from the trajectory using ExtractAgent.

        Args:
            trajectory: The complete trajectory from the React loop
            user_query: The original user query
            user_name: The name of the user

        Returns:
            ExtractAgentActivityResult
        """
        workflow.logger.info(
            "[AgenticAIWorkflow] Extracting final answer from trajectory"
        )

        try:
            return await workflow.execute_activity_method(
                ExtractAgentActivity.run_extract_agent,
                args=[trajectory, user_query, user_name],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )
        except Exception as e:
            workflow.logger.error(
                f"[AgenticAIWorkflow] Error calling ExtractAgent activity: {e}"
            )
            return ExtractAgentActivityResult(
                status=ActivityStatus.ERROR,
                trajectory=trajectory,
                error=str(e)
            )

    @workflow.query
    def get_query_count(self) -> int:
        """Query handler to expose workflow state."""
        return self.query_count

    @workflow.query
    def get_status(self) -> str:
        """Query handler to get workflow status."""
        return f"Workflow has processed {self.query_count} queries"
    
    @workflow.query
    def get_trajectory(self) -> Dict[str, Any]:
        """Query handler to get the current trajectory."""
        return self.trajectory
    
    @workflow.query
    def get_tools_used(self) -> List[str]:
        """Query handler to get the list of tools used."""
        return self.tools_used
    
    @workflow.query
    def get_workflow_details(self) -> Dict[str, Any]:
        """Query handler to get comprehensive workflow details."""
        return {
            "query_count": self.query_count,
            "status": self.workflow_status,
            "current_iteration": self.current_iteration,
            "tools_used": self.tools_used,
            "execution_time": self.execution_time,
            "trajectory_keys": list(self.trajectory.keys()) if self.trajectory else [],
        }
