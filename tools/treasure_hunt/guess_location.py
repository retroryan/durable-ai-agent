"""Guess location tool implementation using the unified base class."""
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class GuessLocationTool(BaseTool):
    """Tool for guessing the treasure location."""

    NAME: ClassVar[str] = "guess_location"
    MODULE: ClassVar[str] = "tools.treasure_hunt.guess_location"

    class Arguments(BaseModel):
        """Argument validation model."""

        address: Optional[str] = Field(
            default="", description="The street address guess"
        )
        city: Optional[str] = Field(default="", description="The city guess")
        state: Optional[str] = Field(default="", description="The state guess")

        def model_post_init(self, __context) -> None:
            """Ensure at least one field is provided."""
            super().model_post_init(__context)
            if not any([self.address, self.city, self.state]):
                # Set default empty strings if nothing provided
                self.address = ""
                self.city = ""
                self.state = ""

    # Tool definition as instance attributes
    description: str = "Guess the treasure location based on address, city, or state"
    args_model: Type[BaseModel] = Arguments

    def execute(
        self, address: str = "", city: str = "", state: str = ""
    ) -> Dict[str, Any]:
        """Execute the tool to check if the guess is correct."""
        # Check if the guess is correct
        if "seattle" in city.lower() and "lenora" in address.lower():
            return {"status": "Correct!", "message": "You found the treasure!"}
        else:
            return {
                "status": "Incorrect",
                "message": "Sorry, that's not the right location.",
            }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="I think the treasure is at the library",
                expected_tools=["guess_location"],
                description="Guessing treasure location",
            ),
            ToolTestCase(
                request="Is it in Seattle on Lenora Street?",
                expected_tools=["guess_location"],
                description="Specific location guess",
            ),
            ToolTestCase(
                request="The treasure must be in Washington state",
                expected_tools=["guess_location"],
                description="State-level guess",
            ),
        ]
