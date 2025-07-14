"""
Base classes for tool sets.

This module defines the core infrastructure for organizing tools into logical groups (tool sets).
Each tool set can contain multiple tools and provides a way to manage and load
collections of tools relevant to specific domains or functionalities.
"""
from typing import Any, ClassVar, Dict, List, Optional, Type

import dspy
from pydantic import BaseModel, ConfigDict, Field

from .base_tool import BaseTool, ToolTestCase


class ToolSetTestCase(ToolTestCase):
    """
    Extends the base ToolTestCase to include tool set-specific metadata.

    This allows test cases to be associated with a particular tool set and
    optionally a scenario within that set, aiding in more organized testing.
    """

    tool_set: str  # The name of the tool set this test case belongs to
    scenario: Optional[
        str
    ] = None  # An optional, more granular grouping for test cases within a tool set
    expected_arguments: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Expected arguments for each tool. Key is tool name, value is dict of arguments.",
    )


class ToolSetConfig(BaseModel):
    """
    Configuration model for a ToolSet.

    This model defines the immutable properties of a tool set, such as its name,
    description, and the list of tool classes it contains.
    """

    model_config = ConfigDict(
        frozen=True
    )  # Ensures the configuration is immutable after creation

    name: str  # The unique name of the tool set (e.g., "treasure_hunt", "productivity")
    description: str  # A brief description of the tool set's purpose
    tool_classes: List[
        Type[BaseTool]
    ]  # A list of direct references to the BaseTool subclasses included in this set


class ToolSet(BaseModel):
    """
    Base class for defining a collection of related tools.

    Subclasses should define their specific tools and provide test cases relevant
    to their domain. Tool sets can also provide custom DSPy signatures for React
    and Extract agents.
    """

    config: ToolSetConfig  # The immutable configuration for this tool set

    def load(self) -> None:
        """
        Legacy method - registration is now handled explicitly via factory functions.

        This method is kept for backward compatibility but does nothing.
        Use the factory functions in shared/tool_set_registry.py instead.
        """
        # No-op - explicit registration is now handled by factory functions
        pass

    def get_loaded_tools(self) -> List[str]:
        """
        Returns a list of names of the tools that are part of this tool set.

        These are the tools that *should* be loaded into the registry when this
        tool set is activated.
        """
        return [tool_class.NAME for tool_class in self.config.tool_classes]

    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Abstract method to be implemented by subclasses.

        Subclasses should return a list of `ToolSetTestCase` objects that are
        specific to the functionality provided by the tools within that set.

        Returns:
            List[ToolSetTestCase]: A list of test cases for the tool set.
        """
        return []

    @classmethod
    def get_react_signature(cls) -> Optional[Type[dspy.Signature]]:
        """
        Return the React signature for this tool set.

        The React signature contains domain-specific requirements for tool execution,
        such as coordinate extraction instructions or precision requirements.

        Returns:
            Optional[Type[dspy.Signature]]: The React signature class, or None to use default behavior
        """
        return None

    @classmethod
    def get_extract_signature(cls) -> Optional[Type[dspy.Signature]]:
        """
        Return the Extract signature for this tool set.

        The Extract signature contains domain input/output fields for final synthesis,
        without any tool-specific instructions.

        Returns:
            Optional[Type[dspy.Signature]]: The Extract signature class, or None to use default behavior
        """
        return None
