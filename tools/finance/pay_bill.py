"""Pay bill tool implementation."""
from typing import List

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolMetadata, ToolTestCase


class PayBillTool(BaseTool):
    """Tool for paying bills."""

    class Arguments(BaseModel):
        """Arguments for paying a bill."""

        biller: str = Field(..., description="Biller name")
        amount: float = Field(..., gt=0, description="Amount to pay")
        account_number: str = Field(..., description="Bill account number")

    metadata = ToolMetadata(
        name="pay_bill",
        description="Pay a bill",
        category="finance",
        args_model=Arguments,
    )

    def execute(self, biller: str, amount: float, account_number: str) -> dict:
        """Execute the tool to pay a bill."""
        return {
            "confirmation": f"Paid ${amount} to {biller}",
            "transaction_id": "PAY789",
            "account_number": account_number,
            "status": "completed",
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Pay $150 to electric company account 12345",
                expected_tools=["pay_bill"],
                description="Pay utility bill",
            ),
            ToolTestCase(
                request="Pay my credit card bill of $500 to Chase account 67890",
                expected_tools=["pay_bill"],
                description="Pay credit card bill",
            ),
        ]
