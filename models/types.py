"""Simple data types for the durable AI agent."""
from typing import Any, Dict, Optional, Union, List, TypeAlias
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field

from models.tool_definitions import MCPServerDefinition
from models.trajectory import Trajectory


class MessageRole(str, Enum):
    """Fixed message roles with no magic strings."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class Message(BaseModel):
    """Simple message with enum role."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


ConversationHistory: TypeAlias = List[Message]


class Response(BaseModel):
    """Response from the workflow."""

    message: str = Field(description="Response message")
    event_count: int = Field(description="Number of events found")
    query_count: int = Field(description="Total queries made in this workflow")

class WorkflowSummary(BaseModel):
    """Summary of a completed workflow."""

    tool_count: int = Field(description="Total tools used in this workflow")
    user_name: str = Field(default=None, description="User name for the conversation")
    execution_time: float = Field(default=0.0, description="Total execution time in seconds")
    trajectory_summary: Optional[Dict[str, Any]] = Field(
        default=None, description="Summary of the trajectory if available"
    )

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
    trajectories: List[Trajectory] = Field(description="List of trajectory steps")
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
    trajectories: List[Trajectory] = Field(description="List of trajectory steps")
    current_iteration: int = Field(description="Current iteration number")


class ToolExecutionResult(BaseModel):
    """Result of executing a single tool."""
    success: bool = Field(
        default=True, description="Whether the tool execution was successful"
    )
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: float = Field(
        default=0, description="Time taken to execute the tool"
    )
    trajectories: Optional[List[Trajectory]] = Field(
        None, description="Updated list of trajectories after tool execution"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage in conversation history."""
        return self.model_dump()

class ExtractAgentActivityResult(BaseModel):
    """Result from ExtractAgentActivity activity execution."""

    status: str = Field(description="Status of the execution: 'success' or 'error'")
    answer: Optional[str] = Field(default=None, description="Extracted final answer")
    reasoning: Optional[str] = Field(
        default=None, description="Chain of thought reasoning for the answer"
    )
    trajectories: List[Trajectory] = Field(description="List of trajectories that were processed")
    error: Optional[str] = Field(
        default=None, description="Error message if status is 'error'"
    )


class WorkflowStatus:
    """Workflow status constants for AgenticAIWorkflow."""
    
    INITIALIZED = "initialized"
    RUNNING_REACT_LOOP = "running_react_loop"
    EXTRACTING_ANSWER = "extracting_answer"
    COMPLETED = "completed"
    FAILED = "failed"


class ActivityStatus:
    """Activity execution status constants."""
    
    SUCCESS = "success"
    ERROR = "error"
    COMPLETED = "completed"


class AgenticAIWorkflowState(BaseModel):
    """Detailed state of the AgenticAIWorkflow."""
    
    workflow_id: str = Field(description="Workflow ID")
    status: str = Field(description="Current workflow status")
    query_count: int = Field(default=0, description="Number of queries processed")
    current_iteration: int = Field(default=0, description="Current iteration in React loop")
    tools_used: list[str] = Field(default_factory=list, description="List of tools used")
    execution_time: float = Field(default=0.0, description="Total execution time in seconds")
    trajectory_keys: list[str] = Field(default_factory=list, description="List of trajectory keys")
    trajectories: List[Trajectory] = Field(default_factory=list, description="List of trajectory steps")
    trajectory: Optional[dict] = Field(default=None, description="Full trajectory data when requested")


class MCPConfig(BaseModel):
    """Configuration for MCP tool execution."""
    
    server_name: str = Field(description="Name identifier for the MCP server")
    tool_name: str = Field(description="Name of the tool in the MCP server")
    server_definition: MCPServerDefinition = Field(description="Server connection details")
