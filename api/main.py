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
from models.types import Response, WorkflowInput, WorkflowState
from shared.config import get_settings

# Create logs directory if it doesn't exist
os.makedirs("/app/logs", exist_ok=True)

# Generate timestamp for log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"/app/logs/api_{timestamp}.log"

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

    settings = get_settings()
    logger.info(f"Connecting to Temporal at {settings.temporal_host}")

    # Create Temporal client
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )

    # Initialize workflow service
    workflow_service = WorkflowService(client, settings.task_queue)
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "temporal_connected": workflow_service is not None,
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
