"""Get order tool implementation using the unified base class."""
import json
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Type

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class GetOrderTool(BaseTool):
    """Tool for retrieving order information by order ID."""

    NAME: ClassVar[str] = "get_order"
    MODULE: ClassVar[str] = "tools.ecommerce.get_order"

    class Arguments(BaseModel):
        """Argument validation model."""

        order_id: str = Field(..., min_length=1, description="The order ID to retrieve")

    # Tool definition as instance attributes
    description: str = "Get order details by order ID"
    args_model: Type[BaseModel] = Arguments

    def execute(self, order_id: str) -> Dict[str, Any]:
        """Execute the tool to get order details."""
        file_path = (
            Path(__file__).resolve().parent.parent / "data" / "customer_order_data.json"
        )
        if not file_path.exists():
            return {"error": "Data file not found."}

        with open(file_path, "r") as file:
            data = json.load(file)
        order_list = data["orders"]

        for order in order_list:
            if order["id"] == order_id:
                return order

        return {"error": f"Order {order_id} not found."}

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Get order details for order 12345",
                expected_tools=["get_order"],
                description="Basic order lookup",
            ),
            ToolTestCase(
                request="I need to check my order ORD-001",
                expected_tools=["get_order"],
                description="Order status check",
            ),
            ToolTestCase(
                request="Show me information about order ABC123",
                expected_tools=["get_order"],
                description="Order information request",
            ),
        ]
