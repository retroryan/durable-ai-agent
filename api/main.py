"""Main FastAPI application for the durable AI agent."""
import logging

# Configure logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from temporalio.client import Client

from api.services.workflow_service import WorkflowService
from models.trajectory import Trajectory
from models.types import Response, WorkflowInput, WorkflowState, AgenticAIWorkflowState
from models.api_models import (
    SendMessageRequest, SendMessageResponse,
    EndConversationResponse, ConversationHistoryResponse,
    WorkflowStatusResponse, SummaryRequestResponse
)
from shared.config import Settings

# Create logs directory if it doesn't exist
# Use local logs directory when running outside Docker
log_dir = "/app/logs" if os.path.exists("/app") else "./logs"
os.makedirs(log_dir, exist_ok=True)

# Generate timestamp for log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"{log_dir}/api_{timestamp}.log"

# Configure logging with both console and file handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console output
        RotatingFileHandler(
            log_filename, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        ),
    ],
)
logger = logging.getLogger(__name__)
logger.info(f"API server logging to: {log_filename}")

from typing import Optional

# Global variables
workflow_service: Optional[WorkflowService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global workflow_service

    config = Settings()
    logger.info(f"Connecting to Temporal at {config.temporal_host}")

    # Create Temporal client
    client = await Client.connect(
        config.temporal_host,
        namespace=config.temporal_namespace,
    )

    # Initialize workflow service
    workflow_service = WorkflowService(client, config.task_queue)
    logger.info("API server started successfully")

    yield

    # Cleanup
    logger.info("Shutting down API server")


# Create FastAPI app
app = FastAPI(
    title="Durable AI Agent API",
    description="Simple API for managing durable conversations with Temporal",
    version="0.1.0",
    lifespan=lifespan,
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging."""
    start_time = time.time()

    # Log the incoming request
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url} "
            f"Status: {response.status_code} Time: {process_time:.4f}s"
        )
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request failed: {request.method} {request.url} "
            f"Error: {str(e)} Time: {process_time:.4f}s"
        )
        return JSONResponse(
            status_code=500, content={"detail": f"Internal server error: {str(e)}"}
        )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Durable AI Agent API",
        "version": "0.1.0",
        "status": "healthy",
    }


@app.post("/chat", response_model=WorkflowState)
async def chat(input_data: WorkflowInput):
    """
    Start a new workflow or send a message to an existing one.

    Args:
        input_data: Workflow input with message and optional workflow_id

    Returns:
        WorkflowState with the current state
    """
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        workflow_id = (
            input_data.workflow_id or f"durable-agent-{__import__('uuid').uuid4()}"
        )
        user_name = input_data.user_name or "anonymous"
        logger.info(
            f"Processing message for workflow_id: {workflow_id}, user_name: {user_name}"
        )

        # Start or signal workflow
        state = await workflow_service.process_message(
            input_data.message,
            input_data.workflow_id,
            user_name,
        )
        logger.info(
            f"Successfully processed message for workflow_id: {state.workflow_id}, status: {state.status}"
        )
        return state
    except Exception as e:
        logger.error(
            f"Error processing message for workflow_id: {input_data.workflow_id}, error: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}/status", response_model=WorkflowState)
async def get_workflow_status(workflow_id: str):
    """
    Get the status of a workflow.

    Args:
        workflow_id: The workflow ID

    Returns:
        WorkflowState with current status
    """
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        logger.info(f"Getting status for workflow_id: {workflow_id}")
        state = await workflow_service.get_workflow_state(workflow_id)
        if not state:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        logger.info(
            f"Retrieved status for workflow_id: {workflow_id}, status: {state.status}"
        )
        return state
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting workflow status for workflow_id: {workflow_id}, error: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}/query")
async def query_workflow(workflow_id: str):
    """
    Query workflow for its current state.

    Args:
        workflow_id: The workflow ID

    Returns:
        Query results including query count and status
    """
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        logger.info(f"Querying workflow_id: {workflow_id}")
        query_count = await workflow_service.get_query_count(workflow_id)
        status = await workflow_service.get_workflow_status_message(workflow_id)

        logger.info(
            f"Query results for workflow_id: {workflow_id}, query_count: {query_count}"
        )
        return {
            "workflow_id": workflow_id,
            "query_count": query_count,
            "status": status,
        }
    except Exception as e:
        logger.error(f"Error querying workflow_id: {workflow_id}, error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}/ai-state", response_model=AgenticAIWorkflowState)
async def get_ai_workflow_state(workflow_id: str, include_trajectory: bool = False):
    """
    Get the detailed state of an AgenticAIWorkflow.
    
    Args:
        workflow_id: The workflow ID
        include_trajectory: Whether to include the full trajectory in the response
        
    Returns:
        AgenticAIWorkflowState with detailed workflow information
    """
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Getting AI workflow state for workflow_id: {workflow_id}")
        
        # Query the workflow for its detailed state
        workflow_details = await workflow_service.get_ai_workflow_details(workflow_id)
        
        if not workflow_details:
            logger.warning(f"AI workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Build the response
        ai_state = AgenticAIWorkflowState(
            workflow_id=workflow_id,
            status=workflow_details.get("status", "unknown"),
            query_count=workflow_details.get("query_count", 0),
            current_iteration=workflow_details.get("current_iteration", 0),
            tools_used=workflow_details.get("tools_used", []),
            execution_time=workflow_details.get("execution_time", 0.0),
            trajectory_keys=workflow_details.get("trajectory_keys", [])
        )
        
        # Include full trajectory if requested
        if include_trajectory:
            trajectory = await workflow_service.get_ai_workflow_trajectory(workflow_id)
            ai_state.trajectory = trajectory
        
        logger.info(
            f"Retrieved AI state for workflow_id: {workflow_id}, "
            f"status: {ai_state.status}, tools_used: {len(ai_state.tools_used)}"
        )
        return ai_state
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting AI workflow state for workflow_id: {workflow_id}, error: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}/ai-trajectories")
async def get_ai_workflow_trajectories(workflow_id: str):
    """
    Get the full trajectories of an AgenticAIWorkflow.
    
    Args:
        workflow_id: The workflow ID
        
    Returns:
        The complete list of trajectories
    """
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Getting AI workflow trajectories for workflow_id: {workflow_id}")
        
        trajectories = await workflow_service.get_ai_workflow_trajectories(workflow_id)
        
        if trajectories is None:
            logger.warning(f"AI workflow trajectories not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logger.info(
            f"Retrieved trajectories for workflow_id: {workflow_id}, "
            f"summary: {Trajectory.summarize_trajectories(trajectories) if trajectories else 'No trajectories'}"
        )
        return {
            "workflow_id": workflow_id,
            "trajectories": trajectories,
            "summary": Trajectory.summarize_trajectories(trajectories) if trajectories else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting AI workflow trajectory for workflow_id: {workflow_id}, error: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}/ai-tools")
async def get_ai_workflow_tools(workflow_id: str):
    """
    Get the list of tools used by an AgenticAIWorkflow.
    
    Args:
        workflow_id: The workflow ID
        
    Returns:
        List of tools used in the workflow
    """
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Getting AI workflow tools for workflow_id: {workflow_id}")
        
        tools_used = await workflow_service.get_ai_workflow_tools(workflow_id)
        
        if tools_used is None:
            logger.warning(f"AI workflow not found: {workflow_id}")
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logger.info(
            f"Retrieved tools for workflow_id: {workflow_id}, "
            f"tools: {tools_used}"
        )
        return {
            "workflow_id": workflow_id,
            "tools_used": tools_used,
            "tool_count": len(tools_used)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting AI workflow tools for workflow_id: {workflow_id}, error: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow/{workflow_id}/message", response_model=SendMessageResponse)
async def send_message(workflow_id: str, request: SendMessageRequest):
    """
    Send a message signal to running workflow.
    
    Note: In the current architecture, workflows complete after processing one message.
    This endpoint is provided for future signal-driven conversation support.
    """
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Sending message to workflow_id: {workflow_id}")
        
        # Use workflow service to send message signal
        success = await workflow_service.send_message_signal(workflow_id, request.message)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found or not running")
        
        return SendMessageResponse(
            status="message sent",
            workflow_id=workflow_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to workflow_id: {workflow_id}, error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow/{workflow_id}/end", response_model=EndConversationResponse)
async def end_conversation(workflow_id: str):
    """End a conversation gracefully."""
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Ending conversation for workflow_id: {workflow_id}")
        
        # Use workflow service to end conversation
        final_state = await workflow_service.end_conversation(workflow_id)
        
        if not final_state:
            raise HTTPException(status_code=404, detail="Workflow not found or not running")
        
        # Get message count from final state
        message_count = len(final_state.get("conversation_history", []))
        
        return EndConversationResponse(
            status="conversation ended",
            final_message_count=message_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending conversation for workflow_id: {workflow_id}, error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}/history", response_model=ConversationHistoryResponse)
async def get_history(workflow_id: str):
    """Query conversation history."""
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Getting conversation history for workflow_id: {workflow_id}")
        
        # Get workflow handle
        handle = workflow_service.client.get_workflow_handle(workflow_id)
        
        # Query conversation history
        history = await handle.query("get_conversation_history")
        
        return ConversationHistoryResponse(
            conversation_history=history,
            total_messages=len(history),
            workflow_id=workflow_id
        )
    except Exception as e:
        logger.error(f"Error getting history for workflow_id: {workflow_id}, error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}/workflow-status", response_model=WorkflowStatusResponse)
async def get_workflow_status_detailed(workflow_id: str):
    """Get detailed workflow status."""
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Getting detailed workflow status for workflow_id: {workflow_id}")
        
        # Get workflow handle
        handle = workflow_service.client.get_workflow_handle(workflow_id)
        
        # Query workflow status
        status = await handle.query("get_workflow_status")
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            is_processing=status.get("is_processing", False),
            should_end=status.get("should_end", False),
            message_count=status.get("message_count", 0),
            pending_messages=status.get("pending_messages", 0),
            interaction_count=status.get("interaction_count", 0)
        )
    except Exception as e:
        logger.error(f"Error getting detailed status for workflow_id: {workflow_id}, error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow/{workflow_id}/request-summary", response_model=SummaryRequestResponse)
async def request_summary(workflow_id: str):
    """Request a conversation summary."""
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        logger.info(f"Requesting summary for workflow_id: {workflow_id}")
        
        # Get workflow handle
        handle = workflow_service.client.get_workflow_handle(workflow_id)
        
        # Signal summary request
        await handle.signal("request_summary")
        
        return SummaryRequestResponse(
            status="summary requested",
            summary_requested=True,
            workflow_id=workflow_id
        )
    except Exception as e:
        logger.error(f"Error requesting summary for workflow_id: {workflow_id}, error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow/{workflow_id}/signal/stop")
async def signal_stop_workflow(workflow_id: str):
    """Send stop signal to workflow."""
    if not workflow_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Get workflow handle
        handle = workflow_service.client.get_workflow_handle(workflow_id)
        
        # Send stop signal
        await handle.signal("stop_workflow")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "signal sent",
                "workflow_id": workflow_id,
                "signal": "stop_workflow",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Error sending stop signal to workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "temporal_connected": workflow_service is not None,
    }


if __name__ == "__main__":
    import uvicorn

    config = Settings()
    uvicorn.run(
        "api.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True,
    )
