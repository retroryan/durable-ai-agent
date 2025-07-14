"""Simple data types for the durable AI agent."""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in the conversation."""

    id: str = Field(description="Unique message ID")
    content: str = Field(description="Message content")
    role: str = Field(description="Message role: 'user' or 'assistant'")


class Response(BaseModel):
    """Response from the workflow."""

    message: str = Field(description="Response message")
    event_count: int = Field(description="Number of events found")
    query_count: int = Field(description="Total queries made in this workflow")


class WorkflowInput(BaseModel):
    """Input parameters for starting a workflow."""

    message: str = Field(description="User message")
    workflow_id: Optional[str] = Field(default=None, description="Optional workflow ID")
    user_name: Optional[str] = Field(
        default=None, description="User name for the conversation"
    )


class WorkflowState(BaseModel):
    """State of a workflow."""

    workflow_id: str = Field(description="Workflow ID")
    status: str = Field(description="Workflow status")
    query_count: int = Field(default=0, description="Number of queries made")
    last_response: Optional[Response] = Field(default=None)


class ReactAgentActivityResult(BaseModel):
    """Result from ReactAgentActivity activity execution."""

    status: str = Field(description="Status of the execution: 'success' or 'error'")
    trajectory: Dict[str, Any] = Field(description="Agent execution trajectory")
    tool_name: str = Field(description="Name of the tool used by the agent")
    tool_args: Optional[Dict[str, Any]] = Field(
        default=None, description="Arguments for the tool call"
    )
    user_name: Optional[str] = Field(
        default=None, description="Display name of the user"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if status is 'error'"
    )


class ToolExecutionRequest(BaseModel):
    """Request for tool execution activity."""

    tool_name: str = Field(description="Name of the tool to execute")
    tool_args: Dict[str, Any] = Field(description="Arguments for the tool")
    trajectory: Dict[str, Any] = Field(description="Current agent trajectory")
    current_iteration: int = Field(description="Current iteration number")


class ExtractAgentActivityResult(BaseModel):
    """Result from ExtractAgentActivity activity execution."""

    status: str = Field(description="Status of the execution: 'success' or 'error'")
    answer: Optional[str] = Field(default=None, description="Extracted final answer")
    reasoning: Optional[str] = Field(
        default=None, description="Chain of thought reasoning for the answer"
    )
    trajectory: Dict[str, Any] = Field(description="Original trajectory that was processed")
    error: Optional[str] = Field(
        default=None, description="Error message if status is 'error'"
    )
