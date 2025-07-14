"""List orders tool implementation using the unified base class."""
import json
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Type

from pydantic import BaseModel, Field, field_validator

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class ListOrdersTool(BaseTool):
    """Tool for listing orders for a customer by email address."""

    NAME: ClassVar[str] = "list_orders"
    MODULE: ClassVar[str] = "tools.ecommerce.list_orders"

    class Arguments(BaseModel):
        """Argument validation model."""

        email_address: str = Field(
            default="{{user_email}}",
            min_length=1,
            description="The customer's email address",
        )

        @field_validator("email_address", mode="before")
        @classmethod
        def validate_email(cls, v) -> str:
            """Basic email validation with support for placeholder values."""
            # Handle None or empty values
            if v is None or v == "" or str(v).lower() == "null":
                return "{{user_email}}"

            # Convert to string if not already
            v = str(v)

            # Allow placeholder values for testing/demo purposes
            if v.startswith("{{") and v.endswith("}}"):
                return v.strip()

            # Regular email validation
            if "@" not in v:
                raise ValueError("Valid email address is required")
            return v.strip()

    # Tool definition as instance attributes
    description: str = "List all orders for a customer by email address"
    args_model: Type[BaseModel] = Arguments

    def execute(self, email_address: str = "{{user_email}}") -> Dict[str, Any]:
        """Execute the tool to list customer orders."""
        # Handle placeholder values for testing/demo
        if email_address.startswith("{{") and email_address.endswith("}}"):
            return {
                "orders": [
                    {
                        "order_id": "ORD123",
                        "order_date": "2024-01-15",
                        "status": "delivered",
                        "total": "$99.99",
                        "items": [
                            {"item_id": "SKU789", "name": "Product Name", "quantity": 1}
                        ],
                    }
                ],
                "note": f"Mock data returned for placeholder email: {email_address}",
            }

        file_path = (
            Path(__file__).resolve().parent.parent / "data" / "customer_order_data.json"
        )
        if not file_path.exists():
            return {"error": "Data file not found."}

        with open(file_path, "r") as file:
            data = json.load(file)
        order_list = data["orders"]

        customer_orders = []
        for order in order_list:
            if order["email"] == email_address:
                customer_orders.append(order)

        if customer_orders:
            # Sort by order date
            customer_orders.sort(key=lambda x: x["order_date"])
            return {"orders": customer_orders}
        else:
            return {"error": f"No orders for customer {email_address} found."}

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Show me all orders for customer@example.com",
                expected_tools=["list_orders"],
                description="Basic order listing",
            ),
            ToolTestCase(
                request="I need to see my order history for john@test.com",
                expected_tools=["list_orders"],
                description="Order history request",
            ),
            ToolTestCase(
                request="List orders for user@domain.com",
                expected_tools=["list_orders"],
                description="List customer orders",
            ),
        ]
