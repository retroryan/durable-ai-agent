"""
Unified base class for tools using Pydantic with built-in metadata.

This module defines the foundational classes for creating tools that can be
registered and used within the DSPy framework for multi-tool selection.
It leverages Pydantic for robust argument validation and clear data modeling.
"""
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, Field


class ToolArgument(BaseModel):
    """
    Represents a single argument for a tool.

    This model is used to define the expected inputs for a tool, including
    its name, type, description, and whether it's required.
    """

    name: str = Field(
        ..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$"
    )  # Valid Python identifier for the argument name
    type: str = Field(
        ...,
        description="Python type name (e.g., 'str', 'int', 'float', 'bool', 'List[str]')",
    )
    description: str = Field(
        ..., min_length=1
    )  # A clear description of what the argument represents
    required: bool = Field(default=True)  # Whether the argument is mandatory
    default: Optional[Any] = None  # Default value if the argument is optional


class BaseTool(BaseModel, ABC):
    """
    Abstract base class for all tools in the system.

    Tools inherit from this class to provide a unified interface for definition,
    argument validation, and execution. It integrates with Pydantic for data
    modeling and validation.
    """

    # Class-level constants (not Pydantic fields) that must be defined by each concrete tool
    NAME: ClassVar[str]  # The unique name of the tool (e.g., "search_products")
    MODULE: ClassVar[
        str
    ]  # The module/category the tool belongs to (e.g., "ecommerce", "productivity")
    
    # Class-level indicator for MCP vs traditional tools
    is_mcp: ClassVar[bool] = False  # Default for all traditional tools

    # Instance fields that define the tool's characteristics
    description: str = Field(
        ..., min_length=1
    )  # A brief explanation of what the tool does
    arguments: List[ToolArgument] = Field(
        default_factory=list
    )  # List of arguments the tool accepts

    # Required: Pydantic model for argument validation.
    # All tools must define this model to specify their expected arguments.
    args_model: Type[BaseModel] = Field(..., exclude=True)
    
    # Configuration for mock behavior (default True to maintain current behavior)
    mock_results: bool = Field(default=True, exclude=True)

    def __init_subclass__(cls, **kwargs):
        """
        Validates that subclasses of BaseTool define the required class variables (NAME, MODULE).
        Also ensures that the NAME is a valid Python identifier.
        """
        super().__init_subclass__(**kwargs)
        # Skip validation for abstract classes
        if ABC in cls.__bases__:
            return
        if not hasattr(cls, "NAME"):
            raise TypeError(f"{cls.__name__} must define a 'NAME' class variable.")
        if not hasattr(cls, "MODULE"):
            raise TypeError(f"{cls.__name__} must define a 'MODULE' class variable.")
        # Validate NAME is a valid Python identifier to ensure it can be used programmatically
        if not cls.NAME.isidentifier():
            raise ValueError(
                f"{cls.__name__}.NAME must be a valid Python identifier, got: '{cls.NAME}'."
            )

    @property
    def name(self) -> str:
        """
        Returns the unique name of the tool, derived from the class-level NAME constant.
        """
        return self.NAME

    def model_post_init(self, __context: Any) -> None:
        """
        Pydantic hook called after model initialization.
        Auto-populates the 'arguments' list from 'args_model'.
        """
        # Extract arguments from the required args_model
        if self.args_model:
            self.arguments = self._extract_arguments_from_model(self.args_model)

    @classmethod
    def _extract_arguments_from_model(
        cls, model: Type[BaseModel]
    ) -> List[ToolArgument]:
        """
        Extracts a list of ToolArgument objects from a Pydantic BaseModel's schema.
        This allows tools to define their arguments using a Pydantic model for convenience.
        """
        schema = model.model_json_schema()  # Get the JSON schema of the Pydantic model
        properties = schema.get("properties", {})  # Extract properties (fields)
        required = schema.get("required", [])  # Get list of required fields

        arguments = []
        for field_name, field_info in properties.items():
            arguments.append(
                ToolArgument(
                    name=field_name,
                    type=field_info.get(
                        "type", "string"
                    ),  # Default to 'string' if type is not specified
                    description=field_info.get("description", ""),
                    required=field_name in required,
                    default=field_info.get("default"),
                )
            )
        return arguments

    def get_argument_list(self) -> List[str]:
        """
        Returns a list of argument names for this tool.

        Returns:
            List of argument names as strings.
        """
        return [arg.name for arg in self.arguments]

    def get_argument_details(self) -> List[Dict[str, Any]]:
        """
        Returns detailed information about each argument.

        Returns:
            List of dictionaries containing argument details.
        """
        return [
            {
                "name": arg.name,
                "type": arg.type,
                "description": arg.description,
                "required": arg.required,
                "default": arg.default,
            }
            for arg in self.arguments
        ]

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Abstract method that must be implemented by all concrete tool classes.
        This method contains the core logic of the tool.

        Args:
            **kwargs: The arguments required for the tool's execution,
                      which will have been validated by 'args_model' if provided.

        Returns:
            A formatted string containing the result of the tool's operation.
        """
        pass

    def validate_and_execute(self, **kwargs) -> str:
        """
        Validates the input arguments using the tool's 'args_model'
        and then executes the tool's logic.

        Returns:
            A formatted string containing the result of the tool's operation.
        """
        # Validate arguments using the Pydantic model
        validated_args = self.args_model(**kwargs)
        # Execute the tool with the validated and dumped arguments
        return self.execute(**validated_args.model_dump())


class ToolTestCase(BaseModel):
    """
    Represents a single test case for evaluating tool selection.

    Used to define a user request and the expected tools that should be selected
    in response to that request.
    """

    request: str  # The user's natural language request
    expected_tools: List[str]  # A list of tool names expected to be selected
    description: str  # A brief description of the test case
