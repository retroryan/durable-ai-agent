"""Add to cart tool implementation using the unified base class."""
from typing import Any, ClassVar, Dict, List, Type

from pydantic import BaseModel, Field, field_validator

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class AddToCartTool(BaseTool):
    """Tool for adding products to shopping cart."""

    NAME: ClassVar[str] = "add_to_cart"
    MODULE: ClassVar[str] = "tools.ecommerce.add_to_cart"

    class Arguments(BaseModel):
        """Arguments for adding to cart."""

        product_id: str = Field(
            default="{{selected_product_from_search}}", description="Product ID"
        )
        quantity: int = Field(default=1, ge=1, description="Quantity to add")

        @field_validator("product_id", mode="before")
        @classmethod
        def validate_product_id(cls, v):
            """Handle placeholder values for product_id."""
            if v is None or v == "None" or v == "" or str(v).lower() == "null":
                # Generate a placeholder product ID for demo purposes
                return "{{selected_product_from_search}}"
            return v

    # Tool definition as instance attributes
    description: str = "Add a product to the shopping cart"
    args_model: Type[BaseModel] = Arguments

    def execute(
        self, product_id: str = "{{selected_product_from_search}}", quantity: int = 1
    ) -> dict:
        """Execute the tool to add product to cart."""
        # Handle placeholder values for demo purposes
        if product_id.startswith("{{") and product_id.endswith("}}"):
            return {
                "cart_total": 2,
                "added": "LAPTOP123",  # Mock product ID
                "quantity": quantity,
                "status": "success",
                "note": f"Mock execution with placeholder: {product_id}",
            }

        return {
            "cart_total": 2,
            "added": product_id,
            "quantity": quantity,
            "status": "success",
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Add product PROD123 to my cart",
                expected_tools=["add_to_cart"],
                description="Add single product",
            ),
            ToolTestCase(
                request="Add 3 units of SKU456 to cart",
                expected_tools=["add_to_cart"],
                description="Add multiple quantities",
            ),
        ]
