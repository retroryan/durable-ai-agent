"""Streaming endpoints for real-time workflow progress monitoring."""
import asyncio
import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from temporalio.client import Client, WorkflowHandle
import logging

logger = logging.getLogger(__name__)


class StreamingEvents:
    """Event types for streaming responses."""
    WORKFLOW_STARTED = "workflow_started"
    PROGRESS_UPDATE = "progress_update"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    ERROR = "error"


def format_sse_event(data: Dict[str, Any]) -> str:
    """
    Format data as a Server-Sent Event.
    
    Args:
        data: Dictionary containing event data
        
    Returns:
        Formatted SSE string
    """
    return f"data: {json.dumps(data)}\n\n"


def create_event(event_type: str, **kwargs) -> Dict[str, Any]:
    """
    Create a standardized event dictionary.
    
    Args:
        event_type: Type of event from StreamingEvents
        **kwargs: Additional event data
        
    Returns:
        Event dictionary with timestamp
    """
    return {
        "event": event_type,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }


async def poll_workflow_progress(
    handle: WorkflowHandle,
    query_method: str,
    poll_interval: float = 0.5
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Poll workflow for progress updates.
    
    Args:
        handle: Temporal workflow handle
        query_method: Name of the query method to call
        poll_interval: Seconds between polls
        
    Yields:
        Progress update events
    """
    last_progress = -1
    
    while True:
        try:
            # Check workflow status
            description = await handle.describe()
            status = description.status.name if description.status else "UNKNOWN"
            
            if status == "RUNNING":
                # Query workflow progress
                progress_info = await handle.query(query_method)
                
                # Only yield if progress changed
                if progress_info.get('progress', -1) != last_progress:
                    last_progress = progress_info['progress']
                    yield create_event(
                        StreamingEvents.PROGRESS_UPDATE,
                        **progress_info
                    )
            
            elif status == "COMPLETED":
                # Get final result
                result = await handle.result()
                yield create_event(
                    StreamingEvents.WORKFLOW_COMPLETED,
                    result=result.__dict__ if hasattr(result, '__dict__') else str(result)
                )
                break
                
            elif status in ["FAILED", "TERMINATED", "CANCELLED"]:
                yield create_event(
                    StreamingEvents.WORKFLOW_FAILED,
                    status=status
                )
                break
                
        except Exception as e:
            logger.error(f"Error polling workflow: {e}")
            yield create_event(
                StreamingEvents.ERROR,
                error=str(e)
            )
            break
        
        await asyncio.sleep(poll_interval)


async def stream_workflow_execution(
    client: Client,
    workflow_class: Any,
    workflow_id: str,
    task_queue: str,
    query_method: str = "get_progress",
    poll_interval: float = 0.5,
    workflow_args: tuple = (),
    workflow_kwargs: dict = None
) -> AsyncGenerator[str, None]:
    """
    Stream workflow execution progress as Server-Sent Events.
    
    Args:
        client: Temporal client
        workflow_class: Workflow class to execute
        workflow_id: Unique workflow ID
        task_queue: Task queue name
        query_method: Query method name for progress
        poll_interval: Seconds between progress polls
        workflow_args: Arguments for workflow
        workflow_kwargs: Keyword arguments for workflow
        
    Yields:
        SSE formatted events
    """
    workflow_kwargs = workflow_kwargs or {}
    
    # Send workflow started event
    yield format_sse_event(
        create_event(
            StreamingEvents.WORKFLOW_STARTED,
            workflow_id=workflow_id
        )
    )
    
    try:
        # Start workflow
        handle = await client.start_workflow(
            workflow_class.run,
            *workflow_args,
            **workflow_kwargs,
            id=workflow_id,
            task_queue=task_queue
        )
        
        # Stream progress updates
        async for event in poll_workflow_progress(handle, query_method, poll_interval):
            yield format_sse_event(event)
            
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        yield format_sse_event(
            create_event(
                StreamingEvents.ERROR,
                error=f"Failed to start workflow: {str(e)}"
            )
        )


class MontyPythonStreaming:
    """Handler for Monty Python workflow streaming."""
    
    def __init__(self, client: Client, task_queue: str):
        """
        Initialize streaming handler.
        
        Args:
            client: Temporal client
            task_queue: Task queue for workflows
        """
        self.client = client
        self.task_queue = task_queue
    
    async def stream(self) -> StreamingResponse:
        """
        Create streaming response for Monty Python workflow.
        
        Returns:
            FastAPI StreamingResponse with SSE events
        """
        # Import here to avoid circular imports
        from workflows.monty_python_workflow import MontyPythonWorkflow
        
        workflow_id = f"monty-python-{uuid.uuid4()}"
        
        async def event_generator():
            """Generate SSE events for the workflow."""
            async for event in stream_workflow_execution(
                client=self.client,
                workflow_class=MontyPythonWorkflow,
                workflow_id=workflow_id,
                task_queue=self.task_queue,
                query_method="get_progress",
                poll_interval=0.5
            ):
                yield event
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable Nginx buffering
            }
        )


def create_streaming_response(
    generator: AsyncGenerator[str, None],
    headers: Optional[Dict[str, str]] = None
) -> StreamingResponse:
    """
    Create a properly configured streaming response.
    
    Args:
        generator: Async generator yielding SSE events
        headers: Optional additional headers
        
    Returns:
        Configured StreamingResponse
    """
    default_headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    }
    
    if headers:
        default_headers.update(headers)
    
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers=default_headers
    )