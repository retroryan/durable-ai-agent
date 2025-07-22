"""Service for managing Temporal workflows."""
import logging
import uuid
import asyncio
from typing import Optional

from temporalio.client import Client, WorkflowHandle
from temporalio.service import RPCError

from models.types import ActivityStatus, Response, WorkflowState
from workflows.agentic_ai_workflow import AgenticAIWorkflow

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
            handle = await self.client.start_workflow(
                AgenticAIWorkflow.run,
                id=workflow_id,
                task_queue=self.task_queue,
            )
            # Send initial message via signal
            await handle.signal("prompt", message)
        
        # Query current state instead of waiting for result
        await asyncio.sleep(0.5)  # Small delay to allow processing
        state_data = await handle.query("state")
        
        # Create workflow state
        state = WorkflowState(
            workflow_id=workflow_id,
            status="running" if is_existing else "started",
            query_count=0,  # AgenticAIWorkflow doesn't track query count
            last_response=Response(
                message=state_data.get("last_response", "Processing your request..."),
                event_count=0,
                query_count=0
            ),
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

            # Get query count
            query_count = 0
            if description.status and description.status.name == "RUNNING":
                try:
                    # AgenticAIWorkflow doesn't have query count, set to 0
                    query_count = 0
                except Exception as e:
                    logger.warning(
                        f"Could not query workflow_id: {workflow_id}, error: {e}"
                    )

            return WorkflowState(
                workflow_id=workflow_id,
                status=description.status.name.lower()
                if description.status
                else "unknown",
                query_count=query_count,
                last_response=None,
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
    
    async def get_conversation_history(self, workflow_id: str) -> Optional[list]:
        """
        Get the conversation history from a workflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            List of messages or None if not found
        """
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            return await handle.query("history")
        except Exception as e:
            logger.error(
                f"Error getting conversation history for workflow_id: {workflow_id}, error: {e}"
            )
            return None
    
    def generate_workflow_id(self) -> str:
        """Generate a new workflow ID."""
        return f"durable-agent-{uuid.uuid4()}"
