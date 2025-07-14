"""Give hint tool implementation using the unified base class."""
from typing import Any, ClassVar, Dict, List, Type

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class GiveHintTool(BaseTool):
    """Tool for giving progressive hints about the treasure location."""

    NAME: ClassVar[str] = "give_hint"
    MODULE: ClassVar[str] = "tools.treasure_hunt.give_hint"

    class Arguments(BaseModel):
        """Argument validation model."""

        hint_total: int = Field(
            default=0, ge=0, description="The total number of hints already given"
        )

    # Tool definition as instance attributes
    description: str = "Give a progressive hint about the treasure location"
    args_model: Type[BaseModel] = Arguments

    def execute(self, hint_total: int = 0) -> Dict[str, Any]:
        """Execute the tool to give a hint."""
        hints = [
            "The treasure is in a city known for its coffee and rain.",
            "It's located near a famous public market.",
            "The address is on a street named after a US President's wife.",
        ]

        if hint_total < len(hints):
            return {"hint": hints[hint_total]}
        else:
            return {"hint": "No more hints available."}

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="I need a hint about the treasure",
                expected_tools=["give_hint"],
                description="Basic hint request",
            ),
            ToolTestCase(
                request="Give me another clue about where the treasure is",
                expected_tools=["give_hint"],
                description="Alternative hint request",
            ),
            ToolTestCase(
                request="Can you help me find the treasure?",
                expected_tools=["give_hint"],
                description="General help request",
            ),
        ]
