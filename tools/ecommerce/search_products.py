"""Search products tool implementation using the unified base class."""
from typing import Any, ClassVar, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, field_validator

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class SearchProductsTool(BaseTool):
    """Tool for searching products in the catalog."""

    NAME: ClassVar[str] = "search_products"
    MODULE: ClassVar[str] = "tools.ecommerce.search_products"

    class Arguments(BaseModel):
        """Arguments for searching products."""

        query: str = Field(..., description="Search query")
        category: Optional[str] = Field(default=None, description="Product category")
        max_price: Optional[float] = Field(
            default=None, ge=0, description="Maximum price"
        )

        @field_validator("max_price", mode="before")
        @classmethod
        def validate_max_price(cls, v) -> Optional[float]:
            """Convert string to float for max_price."""
            if v is None or v == "" or str(v).lower() in ["null", "none"]:
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

    # Tool definition as instance attributes
    description: str = "Search for products in the catalog"
    args_model: Type[BaseModel] = Arguments

    def execute(
        self,
        query: str,
        category: str = None,
        max_price: Union[float, str, None] = None,
    ) -> dict:
        """Execute the tool to search products."""
        # Generate realistic product results based on query
        products = []

        if "gaming keyboard" in query.lower() or "keyboard" in query.lower():
            products = [
                {
                    "id": "KB123",
                    "name": "Gaming Mechanical Keyboard RGB",
                    "price": 129.99,
                    "rating": 4.5,
                },
                {
                    "id": "KB456",
                    "name": "Wireless Gaming Keyboard",
                    "price": 89.99,
                    "rating": 4.2,
                },
                {
                    "id": "KB789",
                    "name": "Pro Gaming Keyboard",
                    "price": 149.99,
                    "rating": 4.8,
                },
            ]
        elif "laptop" in query.lower():
            products = [
                {
                    "id": "LP001",
                    "name": "Gaming Laptop 15-inch",
                    "price": 899.99,
                    "rating": 4.3,
                },
                {
                    "id": "LP002",
                    "name": "Business Laptop",
                    "price": 649.99,
                    "rating": 4.1,
                },
            ]
        else:
            # Generic products for other searches
            products = [
                {
                    "id": "PROD001",
                    "name": f"Product matching '{query}'",
                    "price": 99.99,
                    "rating": 4.0,
                },
                {
                    "id": "PROD002",
                    "name": f"Premium {query}",
                    "price": 199.99,
                    "rating": 4.5,
                },
            ]

        # Apply price filter
        if max_price is not None:
            try:
                max_price_float = float(max_price)
                products = [p for p in products if p["price"] <= max_price_float]
            except (ValueError, TypeError):
                pass  # Skip price filtering if conversion fails

        return {
            "products": products,
            "count": len(products),
            "query": query,
            "best_match": products[0] if products else None,
            "filters": {"category": category, "max_price": max_price},
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Search for laptops under $1000",
                expected_tools=["search_products"],
                description="Search with price filter",
            ),
            ToolTestCase(
                request="Find electronics in the catalog",
                expected_tools=["search_products"],
                description="Search by category",
            ),
            ToolTestCase(
                request="Look for wireless headphones",
                expected_tools=["search_products"],
                description="General product search",
            ),
        ]
