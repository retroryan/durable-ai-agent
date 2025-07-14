"""Transfer money tool implementation."""
from typing import List

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolMetadata, ToolTestCase


class TransferMoneyTool(BaseTool):
    """Tool for transferring money between accounts."""

    class Arguments(BaseModel):
        """Arguments for transferring money."""

        amount: float = Field(..., gt=0, description="Amount to transfer")
        to_account: str = Field(..., description="Destination account")
        from_account: str = Field(..., description="Source account")

    metadata = ToolMetadata(
        name="transfer_money",
        description="Transfer money between accounts or to another person",
        category="finance",
        args_model=Arguments,
    )

    def execute(self, amount: float, to_account: str, from_account: str) -> dict:
        """Execute the tool to transfer money."""
        return {
            "transaction_id": "TXN456",
            "status": "completed",
            "amount": amount,
            "from": from_account,
            "to": to_account,
            "timestamp": "2024-01-01T10:00:00Z",
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Transfer $500 from savings to checking",
                expected_tools=["transfer_money"],
                description="Transfer between accounts",
            ),
            ToolTestCase(
                request="Send $100 to John's account from my checking",
                expected_tools=["transfer_money"],
                description="Transfer to another person",
            ),
        ]
