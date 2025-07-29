"""Service for managing Temporal workflows."""
import logging
import uuid
import asyncio
from typing import Optional

from temporalio.client import Client, WorkflowHandle
from temporalio.service import RPCError

from models.types import ActivityStatus, Response, WorkflowState
from models.conversation import ConversationState, ConversationMessage, ConversationUpdate
from workflows.agentic_ai_workflow import AgenticAIWorkflow
from datetime import timedelta

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing workflow lifecycle."""

    def __init__(self, client: Client, task_queue: str):
        """
        Initialize the workflow service.

        Args:
            client: Temporal client
            task_queue: Task queue name
        """
        self.client = client
        self.task_queue = task_queue

    async def process_message(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        user_name: str = "anonymous",
    ) -> WorkflowState:
        """
        Process a message by starting a new workflow or sending to existing one.

        Args:
            message: The user message
            workflow_id: Optional workflow ID
            user_name: User name for the conversation

        Returns:
            WorkflowState with the result
        """
        logger.info(f"[process_message] Starting with message: {message[:50]}..., workflow_id: {workflow_id}")
        # Generate workflow ID if not provided
        if not workflow_id:
            workflow_id = f"durable-agent-{uuid.uuid4()}"
            logger.info(f"Generated new workflow ID: {workflow_id}")

        try:
            # Try to get existing workflow
            handle = self.client.get_workflow_handle(workflow_id)

            # Check if workflow exists and is running
            try:
                description = await handle.describe()
                if description.status and description.status.name == "RUNNING":
                    logger.info(f"Found running workflow: {workflow_id}")
                    # For now, we'll just execute a new run
                    # In a real system, you might signal the workflow
            except RPCError:
                pass  # Workflow doesn't exist, will create new one
        except Exception:
            handle = None

        # Check if we have an existing workflow running
        is_existing = False
        try:
            # Try to get existing workflow
            handle = self.client.get_workflow_handle(workflow_id)
            description = await handle.describe()
            if description.status and description.status.name == "RUNNING":
                logger.info(f"Found running workflow: {workflow_id}")
                is_existing = True
                # Send message via signal
                await handle.signal("prompt", message)
        except RPCError:
            # Workflow doesn't exist, will create new one
            pass
        
        if not is_existing:
            # Start new workflow
            logger.info(f"Starting new workflow: {workflow_id} for user: {user_name}")
            try:
                handle = await self.client.start_workflow(
                    AgenticAIWorkflow.run,
                    id=workflow_id,
                    task_queue=self.task_queue,
                    execution_timeout=timedelta(minutes=30),
                )
                logger.info(f"[process_message] Workflow started successfully: {workflow_id}")
                # Send initial message via signal
                await handle.signal("prompt", message)
                logger.info(f"[process_message] Signal sent successfully: {workflow_id}")
            except Exception as e:
                logger.error(f"[process_message] Error starting workflow: {e}", exc_info=True)
                raise
        
        # Query current state instead of waiting for result
        
        # Get conversation state using the new query method
        logger.info("About to query get_conversation_state")
        try:
            conv_state = await handle.query("get_conversation_state")
            logger.info(f"Query returned: type={type(conv_state)}, data={conv_state}")
            
            # Pydantic data converter handles all serialization
        except Exception as e:
            logger.error(f"Error querying conversation state: {e}", exc_info=True)
            # Create default state
            conv_state = ConversationState(messages=[], is_processing=True, current_message_id=None)
        
        # Get last response message
        last_message = "Processing your request..."
        
        # Pydantic data converter ensures proper type conversion
        
        try:
            if hasattr(conv_state, 'messages') and conv_state.messages:
                for msg_data in reversed(conv_state.messages):
                    msg = msg_data
                    if msg.is_complete and msg.agent_message:
                        last_message = msg.agent_message
                        break
        except AttributeError as e:
            logger.error(f"AttributeError processing messages: {e}, conv_state type: {type(conv_state)}, conv_state: {conv_state}", exc_info=True)
            # Type is guaranteed by Pydantic data converter
        except Exception as e:
            logger.error(f"Other error processing messages: {e}, conv_state type: {type(conv_state)}", exc_info=True)
        
        # Create workflow state
        state = WorkflowState(
            workflow_id=workflow_id,
            status="running" if is_existing else "started",
            query_count=0,  # AgenticAIWorkflow doesn't track query count
            last_response=Response(
                message=last_message,
                event_count=0,
                query_count=0
            ),
            message_count=0,  # Will be populated on next query
            latest_message=last_message
        )

        return state

    async def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Get the state of a workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            WorkflowState or None if not found
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            description = await handle.describe()

            # Get actual workflow state from query
            last_response = None
            message_count = 0
            latest_message = None
            if description.status and description.status.name == "RUNNING":
                try:
                    # Query the workflow for its current conversation state
                    conv_state = await handle.query("get_conversation_state")
                    logger.info(f"Queried conversation state for {workflow_id}: {conv_state}")
                    
                    # Pydantic data converter handles all serialization
                    
                    # Extract summary data from conversation state
                    message_count = len(conv_state.messages)
                    if conv_state.messages:
                        # Find the latest completed message
                        for msg in reversed(conv_state.messages):
                            if msg.agent_message:
                                latest_message = msg.agent_message
                                last_response = Response(
                                    message=msg.agent_message,
                                    event_count=0,
                                    query_count=0
                                )
                                break
                    
                except Exception as e:
                    logger.warning(
                        f"Could not query workflow state for workflow_id: {workflow_id}, error: {e}"
                    )

            # Determine workflow status based on state
            workflow_status = description.status.name.lower() if description.status else "unknown"
            
            # Check if workflow has completed
            if description.status and description.status.name == "COMPLETED":
                workflow_status = "completed"
            elif description.status and description.status.name == "RUNNING":
                # Workflow is running - it's designed to handle multiple messages
                workflow_status = "running"

            return WorkflowState(
                workflow_id=workflow_id,
                status=workflow_status,
                query_count=0,  # AgenticAIWorkflow doesn't track query count
                last_response=last_response,
                message_count=message_count,
                latest_message=latest_message
            )

        except RPCError:
            return None
        except Exception as e:
            logger.error(
                f"Error getting workflow state for workflow_id: {workflow_id}, error: {e}"
            )
            return None

    async def get_query_count(self, workflow_id: str) -> int:
        """
        Get the query count from a workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            Query count
        """
        try:
            # AgenticAIWorkflow doesn't track query count
            return 0
        except Exception as e:
            logger.error(f"Error querying workflow_id: {workflow_id}, error: {e}")
            return 0

    async def get_workflow_status_message(self, workflow_id: str) -> str:
        """
        Get the status message from a workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            Status message
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            # Query the workflow status from AgenticAIWorkflow
            status_data = await handle.query("status")
            return status_data.get("status", "Unknown")
        except Exception as e:
            logger.error(
                f"Error getting status for workflow_id: {workflow_id}, error: {e}"
            )
            return f"Error: {str(e)}"
    
    async def get_ai_workflow_details(self, workflow_id: str) -> Optional[dict]:
        """
        Get detailed state information from an AgenticAIWorkflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Dictionary with workflow details or None if not found
        """
        try:
            # For AI workflows, the ID pattern includes "agentic-ai-weather-"
            handle = self.client.get_workflow_handle(workflow_id)
            return await handle.query(AgenticAIWorkflow.get_workflow_details)
        except Exception as e:
            logger.error(
                f"Error getting AI workflow details for workflow_id: {workflow_id}, error: {e}"
            )
            return None
    
    async def get_ai_workflow_trajectories(self, workflow_id: str) -> Optional[list]:
        """
        Get the trajectories from an AgenticAIWorkflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            List of trajectories or None if not found
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            return await handle.query(AgenticAIWorkflow.get_trajectories)
        except Exception as e:
            logger.error(
                f"Error getting AI workflow trajectories for workflow_id: {workflow_id}, error: {e}"
            )
            return None
    
    async def get_ai_workflow_trajectory(self, workflow_id: str) -> Optional[dict]:
        """
        Get the full trajectory data from an AgenticAIWorkflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Dictionary containing trajectory data or None if not found
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            trajectories = await handle.query("trajectories")
            return {"trajectories": trajectories} if trajectories else None
        except Exception as e:
            logger.error(
                f"Error getting AI workflow trajectory for workflow_id: {workflow_id}, error: {e}"
            )
            return None
    
    async def get_ai_workflow_tools(self, workflow_id: str) -> Optional[list]:
        """
        Get the list of tools used by an AgenticAIWorkflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            List of tools used or None if not found
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            return await handle.query(AgenticAIWorkflow.get_tools_used)
        except Exception as e:
            logger.error(
                f"Error getting AI workflow tools for workflow_id: {workflow_id}, error: {e}"
            )
            return None
    
    async def send_message_signal(self, workflow_id: str, message: str) -> bool:
        """
        Send a message to a running workflow via signal.
        
        Args:
            workflow_id: The workflow ID
            message: The message to send
            
        Returns:
            True if signal sent successfully, False otherwise
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.signal("prompt", message)
            return True
        except Exception as e:
            logger.error(
                f"Error sending message signal to workflow_id: {workflow_id}, error: {e}"
            )
            return False
    
    async def end_conversation(self, workflow_id: str) -> Optional[dict]:
        """
        End a conversation and get the final state.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Final conversation state or None if error
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.signal("end_chat")
            # Wait a moment for the workflow to process the signal
            await asyncio.sleep(0.5)
            # Get the final result
            result = await handle.result()
            return result
        except Exception as e:
            logger.error(
                f"Error ending conversation for workflow_id: {workflow_id}, error: {e}"
            )
            return None
    
    
    async def get_conversation_updates(self, workflow_id: str, last_seen_message_id: Optional[str] = None) -> Optional[ConversationUpdate]:
        """
        Get conversation updates since last seen message.
        
        Args:
            workflow_id: The workflow ID
            last_seen_message_id: ID of the last message the client has seen
            
        Returns:
            ConversationUpdate or None if not found
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            
            # Query for updates
            updates = await handle.query("get_conversation_updates", last_seen_message_id)
            
            return updates
            
        except Exception as e:
            logger.error(
                f"Error getting conversation updates for workflow_id: {workflow_id}, error: {e}"
            )
            return None
    
    def generate_workflow_id(self) -> str:
        """Generate a new workflow ID."""
        return f"durable-agent-{uuid.uuid4()}"
