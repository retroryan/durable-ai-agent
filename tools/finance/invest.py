"""Invest tool implementation."""
from typing import List

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolMetadata, ToolTestCase


class InvestTool(BaseTool):
    """Tool for investing money."""

    class Arguments(BaseModel):
        """Arguments for investing."""

        amount: float = Field(..., gt=0, description="Amount to invest")
        investment_type: str = Field(
            ..., description="Type of investment (stocks, bonds, funds)"
        )

    metadata = ToolMetadata(
        name="invest",
        description="Invest money in stocks, bonds, or funds",
        category="finance",
        args_model=Arguments,
    )

    def execute(self, amount: float, investment_type: str) -> dict:
        """Execute the tool to invest money."""
        return {
            "investment_id": "INV789",
            "amount": amount,
            "type": investment_type,
            "status": "pending",
            "estimated_return": "7-10% annually",
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Invest $1000 in stocks",
                expected_tools=["invest"],
                description="Invest in stocks",
            ),
            ToolTestCase(
                request="Put $5000 into bonds",
                expected_tools=["invest"],
                description="Invest in bonds",
            ),
        ]
