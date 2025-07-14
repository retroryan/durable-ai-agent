"""
Shared data models for tool selection and agentic loop implementation.

This module contains the combined Pydantic models used by both the tool selection
system and the agentic loop implementation, defining the structure for tool
invocations, decision outputs, and conversation state management.
"""

import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# =============================================================================
# Core Tool Models (originally from tool_selection/models.py)
# =============================================================================


class ToolCall(BaseModel):
    """
    Represents a single invocation of a tool with its specified arguments.

    This model is used to structure the output of the tool selection process,
    indicating which tool should be called and with what parameters.
    """

    tool_name: str = Field(
        ...,
        description="The unique name of the tool to be called (e.g., 'set_reminder')",
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="A dictionary of arguments to pass to the tool, where keys are argument names and values are their corresponding values.",
    )

