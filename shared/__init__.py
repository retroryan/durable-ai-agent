"""
Shared models and utilities for DSPy tool selection and agentic loop.

This module contains the shared models, utilities, and metrics used throughout
the DSPy system for tool selection, agentic loops, and evaluation.
"""

from .console_utils import ConsoleFormatter
from .llm_utils import setup_llm
from .metrics import ToolSelectionMetrics, evaluate_tool_selection

# Import models
from .models import ToolCall  # Tool selection models

__all__ = [
    # Tool selection models
    "ToolCall",
    # Utilities
    "ConsoleFormatter",
    "setup_llm",
    "ToolSelectionMetrics",
    "evaluate_tool_selection",
]
