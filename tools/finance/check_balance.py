"""Check balance tool implementation."""
from typing import List, Optional

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolMetadata, ToolTestCase


class CheckBalanceTool(BaseTool):
    """Tool for checking account balance."""

    class Arguments(BaseModel):
        """Arguments for checking balance."""

        account_type: Optional[str] = Field(
            default="checking", description="Account type (checking, savings)"
        )

    metadata = ToolMetadata(
        name="check_balance",
        description="Check account balance",
        category="finance",
        args_model=Arguments,
    )

    def execute(self, account_type: str = "checking") -> dict:
        """Execute the tool to check balance."""
        return {
            "balance": "$1,234.56",
            "account": account_type,
            "available": "$1,200.00",
            "pending": "$34.56",
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Check my balance",
                expected_tools=["check_balance"],
                description="Check default account balance",
            ),
            ToolTestCase(
                request="What's my savings account balance?",
                expected_tools=["check_balance"],
                description="Check specific account",
            ),
            ToolTestCase(
                request="Show me how much money I have",
                expected_tools=["check_balance"],
                description="General balance inquiry",
            ),
        ]
