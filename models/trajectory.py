"""Trajectory model for agent reasoning steps."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def summarize_trajectories(trajectories: List["Trajectory"]) -> str:
    """
    Generate a summary of trajectories including counts and tools used.
    
    Args:
        trajectories: List of Trajectory objects
        
    Returns:
        A formatted summary string
    """
    if not trajectories:
        return "No trajectories to summarize"
    
    # Count different elements
    thought_count = len(trajectories)
    observation_count = sum(1 for t in trajectories if t.observation is not None)
    error_count = sum(1 for t in trajectories if t.error is not None)
    
    # Get unique tools used (excluding 'error' and 'finish')
    tools_used = []
    for t in trajectories:
        if t.tool_name not in ['error', 'finish'] and t.tool_name not in tools_used:
            tools_used.append(t.tool_name)
    
    # Build summary
    summary_parts = [
        f"Trajectories: {len(trajectories)}",
        f"Thoughts: {thought_count}",
        f"Observations: {observation_count}",
        f"Errors: {error_count}",
        f"Tools used: {', '.join(tools_used) if tools_used else 'None'}"
    ]
    
    return " | ".join(summary_parts)


class Trajectory(BaseModel):
    """Represents a single iteration in the agent's reasoning process."""
    
    iteration: int = Field(description="Iteration number (0-based)")
    thought: str = Field(description="Agent's reasoning for this step")
    tool_name: str = Field(description="Name of the tool to execute")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    observation: Optional[str] = Field(default=None, description="Result from tool execution")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this step occurred")
    
    def is_complete(self) -> bool:
        """Check if this trajectory step has been completed with an observation or error."""
        return self.observation is not None or self.error is not None
    
    @property
    def is_finish(self) -> bool:
        """Check if this is a finish step."""
        return self.tool_name == "finish"
    
    def check_is_finish(self) -> bool:
        """Check if this is a finish step and set observation if it is."""
        if self.tool_name == "finish":
            if self.observation is None:
                self.observation = "Completed."
            return True
        return False