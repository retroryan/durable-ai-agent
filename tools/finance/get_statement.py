"""Get statement tool implementation."""
from typing import List, Optional

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolMetadata, ToolTestCase


class GetStatementTool(BaseTool):
    """Tool for getting account statements."""

    class Arguments(BaseModel):
        """Arguments for getting a statement."""

        account: str = Field(..., description="Account to get statement for")
        period: Optional[str] = Field(
            default="last month", description="Statement period (e.g., 'last month')"
        )

    metadata = ToolMetadata(
        name="get_statement",
        description="Get account statement",
        category="finance",
        args_model=Arguments,
    )

    def execute(self, account: str, period: str = "last month") -> dict:
        """Execute the tool to get a statement."""
        return {
            "account": account,
            "period": period,
            "transactions": 42,
            "starting_balance": "$2,000.00",
            "ending_balance": "$1,234.56",
            "total_deposits": "$3,000.00",
            "total_withdrawals": "$3,765.44",
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Get my checking account statement for last month",
                expected_tools=["get_statement"],
                description="Get monthly statement",
            ),
            ToolTestCase(
                request="Show me my credit card statement",
                expected_tools=["get_statement"],
                description="Get credit card statement",
            ),
        ]
