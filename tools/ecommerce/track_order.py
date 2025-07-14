"""Track order tool implementation using the unified base class."""
from typing import Any, ClassVar, Dict, List, Type

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class TrackOrderTool(BaseTool):
    """Tool for tracking order status."""

    NAME: ClassVar[str] = "track_order"
    MODULE: ClassVar[str] = "tools.ecommerce.track_order"

    class Arguments(BaseModel):
        """Arguments for tracking an order."""

        order_id: str = Field(..., description="Order ID")

    # Tool definition as instance attributes
    description: str = "Track the status of an order"
    args_model: Type[BaseModel] = Arguments

    def execute(self, order_id: str) -> dict:
        """Execute the tool to track an order."""
        return {
            "order_id": order_id,
            "status": "In transit",
            "delivery_date": "Tomorrow",
            "tracking_number": f"TRK{order_id}",
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Track my order ORD789",
                expected_tools=["track_order"],
                description="Track specific order",
            ),
            ToolTestCase(
                request="Where is my package ORDER123?",
                expected_tools=["track_order"],
                description="Check package location",
            ),
        ]
