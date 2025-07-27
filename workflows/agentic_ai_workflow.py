"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from collections import deque
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple, Deque

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models.trajectory import Trajectory
    from models.types import (
        ActivityStatus,
        ExtractAgentActivityResult,
        ReactAgentActivityResult,
        ToolExecutionRequest,
        ToolExecutionResult,
        WorkflowStatus, WorkflowSummary, ConversationHistory, Message, MessageRole,
    )
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
        # Sequential message ID counter - ensures each message gets a unique ID
        # This allows the frontend to track which messages it has already displayed
        self.message_id_counter: int = 0

    @workflow.run
    async def run(self, workflowSummary: Optional[WorkflowSummary] = None) -> ConversationHistory:
        """
        Main workflow execution loop.

        Args:
           workflowSummary: Optional summary of the workflow to initialize state

        Returns:
            ConversationHistory with all messages
        """
        # Initialize from workflow summary if provided
        if workflowSummary:
            self.user_name = workflowSummary.user_name if workflowSummary.user_name else "default_user"
        else:
            self.user_name = "default_user"
        
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
                self.current_iteration += 1

    async def process_prompt_agent_loop(self):
        """Process a single prompt through the agent loop."""
        if not self.prompt_queue:
            return

        try:
            # Peek at the next prompt without removing it
            next_prompt = self.prompt_queue[0] if self.prompt_queue else None

            workflow.logger.info(f"[AgenticAIWorkflow] Processing prompt: {next_prompt}")
            
            # Run the React agent loop (following demo pattern)
            trajectories, execution_time = await self._run_react_loop(
                prompt=next_prompt,
                user_name=self.user_name,
                max_iterations=5
            )
            
            # Update instance state
            self.trajectories = trajectories
            self.execution_time = execution_time

            # Extract final answer
            self.workflow_status = WorkflowStatus.EXTRACTING_ANSWER
            final_answer = await self._extract_final_answer(
                trajectories=trajectories,
                prompt=next_prompt,
                user_name=self.user_name
            )
            
            # Process the result
            response_message = self._format_response(final_answer, trajectories)
            
            # Save to conversation history
            self.message_id_counter += 1
            agent_message = Message(
                id=self.message_id_counter,
                role=MessageRole.AGENT,
                content=response_message,
                timestamp=workflow.now()
            )
            self.conversation_history.append(agent_message)
            
            # Extract tools used from trajectories for logging
            tools_used = Trajectory.get_tools_used_from_trajectories(trajectories)

            # Log summary
            workflow.logger.info(
                f"[AgenticAIWorkflow] Prompt processed successfully. Tools used: {', '.join(tools_used) if tools_used else 'None'}, "
                f"Execution time: {execution_time:.2f}s"
            )
            self.workflow_status = WorkflowStatus.COMPLETED
            prompt = self.prompt_queue.popleft()

        except Exception as e:
            workflow.logger.error(f"[AgenticAIWorkflow] Error processing prompt: {e}")
            self.message_id_counter += 1
            error_message = Message(
                id=self.message_id_counter,
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
    ) -> Tuple[List[Trajectory], float]:
        """
        Run the React agent loop until completion or max iterations.

        Args:
            prompt: The user's query
            user_name: The name of the user
            max_iterations: Maximum number of iterations

        Returns:
            Tuple of (list of trajectories, execution time)
        """
        trajectories: List[Trajectory] = []
        recat_loop_iterations = 1
        start_time = workflow.now()

        workflow.logger.info(
            f"[AgenticAIWorkflow] Starting React agent loop, max iterations: {max_iterations}"
        )

        # Loop until we get "finish" or hit max iterations
        while recat_loop_iterations <= max_iterations:
            workflow.logger.info(
                f"[AgenticAIWorkflow] Iteration {recat_loop_iterations}/{max_iterations}"
            )

            # Call ReactAgent activity
            agent_result = await self._call_react_agent(
                prompt=prompt,
                user_name=user_name,
                trajectories=trajectories,
                current_iteration=recat_loop_iterations
            )

            if agent_result.status != ActivityStatus.SUCCESS:
                workflow.logger.error(
                    f"[AgenticAIWorkflow] ReactAgent failed: {agent_result.error}"
                )
                self.workflow_status = WorkflowStatus.FAILED
                break

            # Update trajectories from agent result
            updated_trajectories = agent_result.trajectories
            
            # Update instance variable for state persistence
            self.trajectories = updated_trajectories

            # Get the latest trajectory (just added by ReactAgent)
            latest_trajectory = updated_trajectories[-1] if updated_trajectories else None
            
            if not latest_trajectory:
                workflow.logger.error("[AgenticAIWorkflow] No trajectory returned from ReactAgent")
                break

            workflow.logger.info(
                f"[AgenticAIWorkflow] Agent Thought - {latest_trajectory.thought} - Tool: {latest_trajectory.tool_name}, Args: {latest_trajectory.tool_args}"
            )

            # Check if we're done
            if latest_trajectory.check_is_finish():
                workflow.logger.info("[AgenticAIWorkflow] Agent selected 'finish' - task complete")
                break

            # Execute the tool
            tool_result = await self._execute_tool(
                trajectories=updated_trajectories,
                current_iteration=recat_loop_iterations
            )

            # Update trajectories with the ones returned by tool execution
            # The ToolExecutionActivity already added the observation
            if tool_result.trajectories:
                self.trajectories = updated_trajectories
                updated_trajectories = tool_result.trajectories

            recat_loop_iterations += 1

        if recat_loop_iterations > max_iterations:
            workflow.logger.warning(
                f"[AgenticAIWorkflow] Reached maximum iterations ({max_iterations})"
            )

        execution_time = (workflow.now() - start_time).total_seconds()
        return updated_trajectories, execution_time

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
        """Signal handler to add new prompts to the queue.
        
        When a user sends a message, it's added to both the prompt queue
        for processing and the conversation history with a unique sequential ID.
        This ensures the frontend can track which messages it has displayed.
        """
        workflow.logger.info(f"[AgenticAIWorkflow] Received prompt signal: {message}")
        self.prompt_queue.append(message)
        # Add user message to conversation history with sequential ID
        self.message_id_counter += 1
        user_message = Message(
            id=self.message_id_counter,
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
    def state(self) -> Dict[str, Any]:
        """Query handler for current state (compatibility with API service).
        
        Returns workflow state including recent conversation history.
        To prevent sending too much data, only the last 10 messages are included.
        Each message has a sequential ID that allows the frontend to track
        which messages it has already displayed.
        """
        latest_msg = self.get_latest_response()
        # Return only last 10 messages to avoid sending too much data
        recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        # Convert Message objects to dicts for proper JSON serialization
        # Use mode='json' to ensure enums are serialized as their values
        serialized_history = [msg.model_dump(mode='json') for msg in recent_history]
        
        # Log what we're returning for debugging
        workflow.logger.info(f"[AgenticAIWorkflow.state] Returning {len(serialized_history)} messages")
        if serialized_history:
            workflow.logger.info(f"[AgenticAIWorkflow.state] First message: id={serialized_history[0].get('id')}, role={serialized_history[0].get('role')}")
            workflow.logger.info(f"[AgenticAIWorkflow.state] Last message: id={serialized_history[-1].get('id')}, role={serialized_history[-1].get('role')}")
        
        result = {
            "last_response": latest_msg.content if latest_msg else "Processing your request...",
            "status": self.workflow_status,
            "conversation_history": serialized_history,
            "pending_prompts": len(self.prompt_queue),
            "is_processing": self.workflow_status == WorkflowStatus.RUNNING_REACT_LOOP
        }
        
        return result
    
    @workflow.query
    def get_conversation_history(self) -> ConversationHistory:
        """Query handler to get the full conversation history."""
        workflow.logger.info(f"[AgenticAIWorkflow.get_conversation_history] Returning {len(self.conversation_history)} messages")
        if self.conversation_history:
            # Log details about messages for debugging
            for i, msg in enumerate(self.conversation_history):
                workflow.logger.info(
                    f"[AgenticAIWorkflow.get_conversation_history] Message {i}: "
                    f"id={msg.id}, role={msg.role.value}, content_preview={msg.content[:50]}..."
                )
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
        return Trajectory.get_tools_used_from_trajectories(self.trajectories)

    @workflow.query
    def get_workflow_details(self) -> Dict[str, Any]:
        """Query handler to get comprehensive workflow details."""
        tools_used = Trajectory.get_tools_used_from_trajectories(self.trajectories)
        return {
            "status": self.workflow_status,
            "user_name": self.user_name,
            "message_count": len(self.conversation_history),
            "pending_prompts": len(self.prompt_queue),
            "current_iteration": self.current_iteration,
            "tools_used": tools_used,
            "execution_time": self.execution_time,
            "trajectory_count": len(self.trajectories),
        }
