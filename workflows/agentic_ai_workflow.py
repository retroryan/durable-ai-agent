"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from collections import deque
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple, Deque

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from models.trajectory import Trajectory
    from models.conversation import ConversationMessage, ConversationState, ConversationUpdate
    from models.types import (
        ActivityStatus,
        ExtractAgentActivityResult,
        ReactAgentActivityResult,
        ToolExecutionRequest,
        ToolExecutionResult,
        WorkflowStatus, WorkflowSummary,
    )
    from activities.extract_agent_activity import ExtractAgentActivity
    from activities.react_agent_activity import ReactAgentActivity
    from activities.tool_execution_activity import ToolExecutionActivity


@workflow.defn
class AgenticAIWorkflow:
    """Signal-driven workflow that processes prompts through a React agent loop."""

    def __init__(self):
        """Initialize workflow state.
        """
        workflow.logger.info("[AgenticAIWorkflow] Initializing workflow state")
        # Trajectory state - automatically persisted by Temporal
        self.trajectories: List[Trajectory] = []
        self.current_iteration = 0
        self.execution_time = 0.0
        self.workflow_status = WorkflowStatus.INITIALIZED
        self.user_name: str = "default_user"
        self.chat_ended: bool = False
        
        # New conversation management
        self.conversation_messages: List[ConversationMessage] = []
        self.pending_user_message: Optional[str] = None
        self.current_message_id: Optional[str] = None
        self.is_processing: bool = False
        workflow.logger.info("[AgenticAIWorkflow] Workflow state initialized successfully")

    @workflow.run
    async def run(self, workflowSummary: Optional[WorkflowSummary] = None) -> List[ConversationMessage]:
        """
        Main workflow execution loop.

        Args:
           workflowSummary: Optional summary of the workflow to initialize state

        Returns:
            List of ConversationMessage objects
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
                lambda: self.pending_user_message is not None or self.chat_ended
            )
            
            # Check if chat should end
            if self.chat_ended:
                workflow.logger.info("[AgenticAIWorkflow] Chat ending, returning conversation messages")
                return self.conversation_messages
                
            # Process pending message
            if self.pending_user_message:
                await self.process_prompt_agent_loop()
                self.current_iteration += 1

    async def process_prompt_agent_loop(self):
        """Process a single prompt through the agent loop."""
        if not self.pending_user_message:
            return

        # Create conversation message when we start processing
        conversation_msg = ConversationMessage(
            user_message=self.pending_user_message,
            user_timestamp=workflow.now()
        )
        self.current_message_id = conversation_msg.id
        self.conversation_messages.append(conversation_msg)
        self.is_processing = True
        self.workflow_status = WorkflowStatus.RUNNING_REACT_LOOP

        try:
            workflow.logger.info(f"[AgenticAIWorkflow] Processing prompt: {self.pending_user_message}")
            
            # Run the React agent loop
            # NOTE: _run_react_loop modifies self.trajectories directly (instance variable)
            execution_time = await self._run_react_loop(
                prompt=self.pending_user_message,
                user_name=self.user_name
            )
            
            # Only update the execution time (trajectories already updated internally)
            self.execution_time = execution_time

            # Extract final answer using the trajectories from instance variable
            self.workflow_status = WorkflowStatus.EXTRACTING_ANSWER
            final_answer = await self._extract_final_answer(
                trajectories=self.trajectories,
                prompt=self.pending_user_message,
                user_name=self.user_name
            )
            
            # Process the result
            response_message = self._format_response(final_answer, self.trajectories)
            
            # Update the conversation message with response
            conversation_msg.agent_message = response_message
            conversation_msg.agent_timestamp = workflow.now()
            conversation_msg.tools_used = Trajectory.get_tools_used_from_trajectories(self.trajectories)
            conversation_msg.processing_time_ms = int(
                (conversation_msg.agent_timestamp - conversation_msg.user_timestamp).total_seconds() * 1000
            )
            
            # Extract tools used from trajectories for logging
            tools_used = conversation_msg.tools_used

            # Log summary
            workflow.logger.info(
                f"[AgenticAIWorkflow] Prompt processed successfully. Tools used: {', '.join(tools_used) if tools_used else 'None'}, "
                f"Execution time: {execution_time:.2f}s"
            )
            # Set status to waiting for next message
            self.workflow_status = WorkflowStatus.WAITING_FOR_INPUT

        except Exception as e:
            workflow.logger.error(f"[AgenticAIWorkflow] Error processing prompt: {e}")
            conversation_msg.error = str(e)
            conversation_msg.agent_timestamp = workflow.now()
            self.workflow_status = WorkflowStatus.FAILED
        
        finally:
            self.pending_user_message = None
            self.current_message_id = None
            self.is_processing = False


    async def _run_react_loop(
        self,
        prompt: str,
        user_name: str
    ) -> float:
        """
        Run the React agent loop until completion or max iterations.
        
        This method directly modifies self.trajectories (instance variable)
        rather than using local variables. This ensures Temporal can properly persist
        and recover state during workflow execution and replays.

        Args:
            prompt: The user's query
            user_name: The name of the user

        Returns:
            float: The execution time in seconds (trajectories are updated via instance variable)
        """
        # Reset trajectories for this new prompt
        self.trajectories = []
        recat_loop_iterations = 1
        start_time = workflow.now()
        MAX_ITERATIONS = 10  # Default max iterations - todo make configurable

        workflow.logger.info(
            f"[AgenticAIWorkflow] Starting React agent loop, max iterations: {MAX_ITERATIONS}"
        )

        # Loop until we get "finish" or hit max iterations
        while recat_loop_iterations <= MAX_ITERATIONS:
            workflow.logger.info(
                f"[AgenticAIWorkflow] Iteration {recat_loop_iterations}/{MAX_ITERATIONS}"
            )
            
            # Log current trajectories state
            workflow.logger.info(
                f"[AgenticAIWorkflow] Current trajectories count before ReactAgent: {len(self.trajectories)}"
            )
            for i, traj in enumerate(self.trajectories):
                workflow.logger.info(
                    f"[AgenticAIWorkflow] Pre-React Trajectory[{i}]: "
                    f"tool={traj.tool_name}, has_observation={traj.observation is not None}"
                )

            # Call ReactAgent activity
            agent_result = await self._call_react_agent(
                prompt=prompt,
                user_name=user_name,
                trajectories=self.trajectories,
                current_iteration=recat_loop_iterations
            )

            if agent_result.status != ActivityStatus.SUCCESS:
                workflow.logger.error(
                    f"[AgenticAIWorkflow] ReactAgent failed: {agent_result.error}"
                )
                self.workflow_status = WorkflowStatus.FAILED
                break

            self.trajectories = agent_result.trajectories

            # Get the latest trajectory (just added by ReactAgent)
            latest_trajectory = self.trajectories[-1] if self.trajectories else None
            
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
                trajectories=self.trajectories,
                current_iteration=recat_loop_iterations
            )

            # Update trajectories with tool execution results
            # The ToolExecutionActivity adds the observation to the last trajectory
            # and returns the complete updated list
            if tool_result.trajectories:
                workflow.logger.info(
                    f"[AgenticAIWorkflow] Tool execution updated trajectories from "
                    f"{len(self.trajectories)} to {len(tool_result.trajectories)}"
                )
                # Update the instance variable so the next iteration sees the observation
                self.trajectories = tool_result.trajectories
            else:
                workflow.logger.warning(
                    "[AgenticAIWorkflow] Tool execution did not return trajectories!"
                )
            
            # Log trajectory state after tool execution
            workflow.logger.info(
                f"[AgenticAIWorkflow] After tool execution, trajectories count: {len(self.trajectories)}"
            )
            if self.trajectories and self.trajectories[-1].observation:
                workflow.logger.info(
                    f"[AgenticAIWorkflow] Latest observation added: "
                    f"{str(self.trajectories[-1].observation)[:100]}..."
                )

            recat_loop_iterations += 1

        if recat_loop_iterations > MAX_ITERATIONS:
            workflow.logger.warning(
                f"[AgenticAIWorkflow] Reached maximum iterations ({MAX_ITERATIONS})"
            )

        execution_time = (workflow.now() - start_time).total_seconds()
        return execution_time

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
        """Signal handler to queue a message for processing.
        
        Messages are not stored until processing begins.
        """
        workflow.logger.info(f"[AgenticAIWorkflow] Received prompt signal: {message}")
        self.pending_user_message = message

    @workflow.signal  
    async def end_chat(self):
        """Signal handler to end the chat."""
        workflow.logger.info("[AgenticAIWorkflow] Received end_chat signal")
        self.chat_ended = True

    @workflow.query
    def get_conversation_state(self) -> ConversationState:
        """Get complete conversation state - use for initial load."""
        return ConversationState(
            messages=self.conversation_messages,
            is_processing=self.is_processing,
            current_message_id=self.current_message_id
        )
    
    @workflow.query
    def get_conversation_updates(self, last_seen_message_id: Optional[str] = None) -> ConversationUpdate:
        """Get updates since last seen message - use for polling."""
        if not last_seen_message_id:
            # First request, return all messages
            return ConversationUpdate(
                new_messages=self.conversation_messages,
                updated_messages=[],
                is_processing=self.is_processing,
                current_message_id=self.current_message_id,
                last_seen_message_id=self.conversation_messages[-1].id if self.conversation_messages else None
            )
        
        # Find messages after last_seen_message_id
        new_messages = []
        updated_messages = []
        found_last_seen = False
        
        for msg in self.conversation_messages:
            if found_last_seen:
                new_messages.append(msg)
            elif msg.id == last_seen_message_id:
                found_last_seen = True
                # Check if this message was updated since last seen
                if not msg.is_complete and msg.agent_message:
                    updated_messages.append(msg)
        
        return ConversationUpdate(
            new_messages=new_messages,
            updated_messages=updated_messages,
            is_processing=self.is_processing,
            current_message_id=self.current_message_id,
            last_seen_message_id=self.conversation_messages[-1].id if self.conversation_messages else last_seen_message_id
        )

    @workflow.query
    def get_latest_response(self) -> Optional[ConversationMessage]:
        """Get the latest completed conversation message."""
        for msg in reversed(self.conversation_messages):
            if msg.is_complete:
                return msg
        return None
    
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
            "message_count": len(self.conversation_messages),
            "pending_message": self.pending_user_message is not None,
            "current_iteration": self.current_iteration,
            "tools_used": tools_used,
            "execution_time": self.execution_time,
            "trajectory_count": len(self.trajectories),
        }
    
