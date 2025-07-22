"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from collections import deque
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple, Deque

from temporalio import workflow
from temporalio.common import RetryPolicy

from models.trajectory import Trajectory
from models.types import (
    ActivityStatus,
    ExtractAgentActivityResult,
    ReactAgentActivityResult,
    ToolExecutionRequest,
    ToolExecutionResult,
    WorkflowStatus, WorkflowSummary, ConversationHistory, Message, MessageRole,
)

with workflow.unsafe.imports_passed_through():
    from activities.extract_agent_activity import ExtractAgentActivity
    from activities.react_agent_activity import ReactAgentActivity
    from activities.tool_execution_activity import ToolExecutionActivity


@workflow.defn
class AgenticAIWorkflow:
    """Signal-driven workflow that processes prompts through a React agent loop."""

    def __init__(self):
        """Initialize workflow state."""
        self.trajectories: List[Trajectory] = []
        self.current_iteration = 0
        self.execution_time = 0.0
        self.workflow_status = WorkflowStatus.INITIALIZED
        self.prompt_queue: Deque[str] = deque()
        self.user_name: str = "default_user"
        self.chat_ended: bool = False
        self.conversation_history: ConversationHistory = []

    @workflow.run
    async def run(self, workflowSummary: WorkflowSummary) -> ConversationHistory:
        """
        Main workflow execution loop.

        Args:
           workflowSummary: Summary of the workflow to initialize state

        Returns:
            ConversationHistory with all messages
        """
        # Initialize from workflow summary
        self.user_name = workflowSummary.get("user_name", "default_user")
        
        workflow.logger.info(
            f"[AgenticAIWorkflow] Starting workflow for user: {self.user_name}, "
            f"workflow_id: {workflow.info().workflow_id}"
        )
        
        # Main event loop
        while True:
            # Wait for prompt or end signal
            await workflow.wait_condition(
                lambda: bool(self.prompt_queue) or self.chat_ended
            )
            
            # Check if chat should end
            if self.chat_ended:
                workflow.logger.info("[AgenticAIWorkflow] Chat ending, returning conversation history")
                return self.conversation_history
                
            # Process pending prompts
            if self.prompt_queue:
                await self.process_prompt_agent_loop()

    async def process_prompt_agent_loop(self):
        """Process a single prompt through the agent loop."""
        if not self.prompt_queue:
            return
            
        # Get and remove prompt from queue
        prompt = self.prompt_queue.popleft()
        
        try:
            workflow.logger.info(f"[AgenticAIWorkflow] Processing prompt: {prompt}")
            
            # Run the React agent loop (following demo pattern)
            trajectories, tools_used, execution_time = await self._run_react_loop(
                prompt=prompt,
                user_name=self.user_name,
                max_iterations=5
            )
            
            # Update instance state
            self.trajectories = trajectories
            self.tools_used = tools_used
            self.execution_time = execution_time

            # Extract final answer
            self.workflow_status = WorkflowStatus.EXTRACTING_ANSWER
            final_answer = await self._extract_final_answer(
                trajectories=trajectories,
                prompt=prompt,
                user_name=self.user_name
            )
            
            # Process the result
            response_message = self._format_response(final_answer, trajectories)
            
            # Save to conversation history
            agent_message = Message(
                role=MessageRole.AGENT,
                content=response_message,
                timestamp=workflow.now()
            )
            self.conversation_history.append(agent_message)
            
            # Log summary
            workflow.logger.info(
                f"[AgenticAIWorkflow] Prompt processed successfully. Tools used: {', '.join(tools_used) if tools_used else 'None'}, "
                f"Execution time: {execution_time:.2f}s"
            )
            self.workflow_status = WorkflowStatus.COMPLETED
            
        except Exception as e:
            workflow.logger.error(f"[AgenticAIWorkflow] Error processing prompt: {e}")
            error_message = Message(
                role=MessageRole.AGENT,
                content=f"Error processing prompt: {e}",
                timestamp=workflow.now()
            )
            self.conversation_history.append(error_message)
            self.workflow_status = WorkflowStatus.FAILED

    async def _run_react_loop(
        self,
        prompt: str,
        user_name: str,
        max_iterations: int = 5
    ) -> Tuple[List[Trajectory], List[str], float]:
        """
        Run the React agent loop until completion or max iterations.

        Args:
            prompt: The user's query
            user_name: The name of the user
            max_iterations: Maximum number of iterations

        Returns:
            Tuple of (list of trajectories, tools used list, execution time)
        """
        trajectories: List[Trajectory] = []
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
                prompt=prompt,
                user_name=user_name,
                trajectories=trajectories,
                current_iteration=current_iteration
            )

            if agent_result.status != ActivityStatus.SUCCESS:
                workflow.logger.error(
                    f"[AgenticAIWorkflow] ReactAgent failed: {agent_result.error}"
                )
                self.workflow_status = WorkflowStatus.FAILED
                break

            # Update trajectories from agent result
            trajectories = agent_result.trajectories
            
            # Update instance variable for state persistence
            self.trajectories = trajectories
            self.current_iteration = current_iteration

            # Get the latest trajectory (just added by ReactAgent)
            latest_trajectory = trajectories[-1] if trajectories else None
            
            if not latest_trajectory:
                workflow.logger.error("[AgenticAIWorkflow] No trajectory returned from ReactAgent")
                break

            workflow.logger.info(
                f"[AgenticAIWorkflow] Agent decision - Tool: {latest_trajectory.tool_name}, Args: {latest_trajectory.tool_args}"
            )

            # Check if we're done
            if latest_trajectory.check_is_finish():
                workflow.logger.info("[AgenticAIWorkflow] Agent selected 'finish' - task complete")
                break

            # Execute the tool
            tool_result = await self._execute_tool(
                trajectories=trajectories,
                current_iteration=current_iteration
            )

            # Update trajectories with the ones returned by tool execution
            # The ToolExecutionActivity already added the observation
            if tool_result.trajectories:
                trajectories = tool_result.trajectories
            
            # Track tools used
            if latest_trajectory.tool_name and not latest_trajectory.is_finish:
                tools_used.append(latest_trajectory.tool_name)

            current_iteration += 1

        if current_iteration > max_iterations:
            workflow.logger.warning(
                f"[AgenticAIWorkflow] Reached maximum iterations ({max_iterations})"
            )

        execution_time = (workflow.now() - start_time).total_seconds()
        return trajectories, tools_used, execution_time

    async def _call_react_agent(
        self,
        prompt: str,
        user_name: str,
        trajectories: List[Trajectory],
        current_iteration: int
    ) -> ReactAgentActivityResult:
        """
        Call the ReactAgent activity with proper error handling.

        Args:
            prompt: The user's prompt
            user_name: The name of the user
            trajectories: Current list of trajectory steps
            current_iteration: Current iteration number

        Returns:
            ReactAgentActivityResult
        """
        try:
            # Call the activity with all required parameters
            result = await workflow.execute_activity_method(
                ReactAgentActivity.run_react_agent,
                args=[prompt, current_iteration, trajectories, user_name],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
            )
            
            workflow.logger.debug(
                f"[AgenticAIWorkflow] ReactAgent returned {len(result.trajectories)} trajectories"
            )
            
            return result
        except Exception as e:
            workflow.logger.error(
                f"[AgenticAIWorkflow] Error calling ReactAgent activity: {e}"
            )
            raise

    async def _execute_tool(
        self,
        trajectories: List[Trajectory],
        current_iteration: int
    ) -> ToolExecutionResult:
        """
        Execute a tool using the ToolExecutionActivity.

        Args:
            trajectories: Current list of trajectory steps
            current_iteration: Current iteration number

        Returns:
            ToolExecutionResult
        """

        latest_trajectory = trajectories[-1] if trajectories else None
        if not latest_trajectory or not latest_trajectory.tool_name:
            workflow.logger.error(
                "[AgenticAIWorkflow] No valid tool name found in latest trajectory"
            )
            return ToolExecutionResult(
                success=False,
                error="No valid tool name found",
                execution_time=0.0,
                trajectories=trajectories,
            )

        workflow.logger.info(
            f"[AgenticAIWorkflow] Executing tool: {latest_trajectory.tool_name} with args: {latest_trajectory.tool_args}"
        )

        tool_request = ToolExecutionRequest(
            tool_name=latest_trajectory.tool_name,
            tool_args=latest_trajectory.tool_args,
            trajectories=trajectories,
            current_iteration=current_iteration
        )

        try:
            # ToolExecutionActivity now returns a ToolExecutionResult object
            result = await workflow.execute_activity_method(
                ToolExecutionActivity.execute_tool,
                args=[tool_request],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    maximum_attempts=3,
                ),
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
                success=False,
                error=str(e),
                trajectories=trajectories,
                execution_time=0.0
            )

    async def _extract_final_answer(
        self,
        trajectories: List[Trajectory],
        prompt: str,
        user_name: str
    ) -> ExtractAgentActivityResult:
        """
        Extract the final answer from the trajectory using ExtractAgent.

        Args:
            trajectories: The complete list of trajectories from the React loop
            prompt: The original user query
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
                args=[trajectories, prompt, user_name],
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
                trajectories=trajectories,
                error=str(e)
            )

    def _format_response(self, final_answer: ExtractAgentActivityResult, trajectories: List[Trajectory]) -> str:
        """Format the final response based on extraction results."""
        if final_answer.status == ActivityStatus.SUCCESS and final_answer.answer:
            return final_answer.answer
        elif final_answer.status == ActivityStatus.SUCCESS:
            # Fallback to latest meaningful observation
            for traj in reversed(trajectories):
                if traj.observation and not traj.observation.startswith("Error:") and traj.observation != "Completed.":
                    return traj.observation
            return "No result found"
        else:
            return f"Error: {final_answer.error or 'Unknown error'}"


    @workflow.signal
    async def prompt(self, message: str):
        """Signal handler to add new prompts to the queue."""
        workflow.logger.info(f"[AgenticAIWorkflow] Received prompt signal: {message}")
        self.prompt_queue.append(message)
        # Add user message to conversation history
        user_message = Message(
            role=MessageRole.USER,
            content=message,
            timestamp=workflow.now()
        )
        self.conversation_history.append(user_message)

    @workflow.signal  
    async def end_chat(self):
        """Signal handler to end the chat."""
        workflow.logger.info("[AgenticAIWorkflow] Received end_chat signal")
        self.chat_ended = True

    @workflow.query
    def get_conversation_history(self) -> ConversationHistory:
        """Query handler to get the full conversation history."""
        return self.conversation_history

    @workflow.query
    def get_latest_response(self) -> Optional[Message]:
        """Get the latest agent response."""
        for msg in reversed(self.conversation_history):
            if msg.role == MessageRole.AGENT:
                return msg
        return None

    @workflow.query
    def get_pending_prompts(self) -> List[str]:
        """Get list of prompts waiting to be processed."""
        return list(self.prompt_queue)
    
    @workflow.query
    def get_workflow_status(self) -> str:
        """Query handler to get current workflow status."""
        return self.workflow_status
    
    @workflow.query
    def get_trajectories(self) -> List[Trajectory]:
        """Query handler to get the current trajectories."""
        return self.trajectories
    
    @workflow.query
    def get_tools_used(self) -> List[str]:
        """Query handler to get the list of tools used."""
        return self.tools_used
    
    @workflow.query
    def get_workflow_details(self) -> Dict[str, Any]:
        """Query handler to get comprehensive workflow details."""
        return {
            "status": self.workflow_status,
            "user_name": self.user_name,
            "message_count": len(self.conversation_history),
            "pending_prompts": len(self.prompt_queue),
            "current_iteration": self.current_iteration,
            "tools_used": self.tools_used,
            "execution_time": self.execution_time,
            "trajectory_count": len(self.trajectories),
        }
