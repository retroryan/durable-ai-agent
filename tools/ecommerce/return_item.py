"""Return item tool implementation using the unified base class."""
from typing import Any, ClassVar, Dict, List, Type

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class ReturnItemTool(BaseTool):
    """Tool for returning items for refund or exchange."""

    NAME: ClassVar[str] = "return_item"
    MODULE: ClassVar[str] = "tools.ecommerce.return_item"

    class Arguments(BaseModel):
        """Arguments for returning an item."""

        order_id: str = Field(..., description="Order ID")
        item_id: str = Field(..., description="Item ID to return")
        reason: str = Field(..., description="Return reason")

    # Tool definition as instance attributes
    description: str = "Return an item for refund or exchange"
    args_model: Type[BaseModel] = Arguments

    def execute(self, order_id: str, item_id: str, reason: str) -> dict:
        """Execute the tool to return an item."""
        return {
            "return_id": "RET456",
            "status": "processing",
            "refund_amount": "$99.99",
            "order_id": order_id,
            "item_id": item_id,
            "reason": reason,
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Return item ITEM123 from order ORD456 because it's defective",
                expected_tools=["return_item"],
                description="Return defective item",
            ),
            ToolTestCase(
                request="I want to return SKU789 from my last order, wrong size",
                expected_tools=["list_orders", "return_item"],
                description="Return for size issue",
            ),
        ]
