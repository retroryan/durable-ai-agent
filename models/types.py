"""Simple data types for the durable AI agent."""
from typing import Optional

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
