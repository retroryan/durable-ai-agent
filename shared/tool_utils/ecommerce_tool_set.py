from datetime import datetime, timedelta
from typing import ClassVar, List, Optional, Type

import dspy

from .base_tool_sets import ToolSet, ToolSetConfig, ToolSetTestCase


class EcommerceReactSignature(dspy.Signature):
    """E-commerce tool execution requirements.

    CURRENT DATE: {current_date}

    E-COMMERCE GUIDELINES:
    - Always use specific identifiers when referencing orders, products, or customers
    - For product searches, be flexible with search terms and filters
    - When tracking orders, use exact order IDs when provided

    ORDER MANAGEMENT PRECISION:
    - Order IDs typically follow patterns like "ORD123", "12345", or alphanumeric codes
    - Customer emails should be validated format (user@domain.com)
    - Product SKUs are usually alphanumeric codes
    - Tracking numbers may have various formats depending on carrier

    PRODUCT SEARCH OPTIMIZATION:
    - Support partial product name matching
    - Allow price range filtering
    - Enable category-based searches
    - Handle brand and feature-specific queries

    CUSTOMER SUPPORT WORKFLOW:
    - For returns, always verify order details first
    - Provide clear reason codes for cancellations/returns
    - Include relevant order information in responses
    - Handle edge cases like expired return windows

    CART OPERATIONS:
    - Validate product availability before adding to cart
    - Handle quantity specifications properly
    - Support multiple items in single operations when applicable

    Use precise identifiers and maintain data consistency across operations.
    """

    user_query: str = dspy.InputField(
        desc="E-commerce query that may reference orders, products, customers, or shopping operations"
    )


class EcommerceExtractSignature(dspy.Signature):
    """Synthesize e-commerce information into user-friendly responses.

    Take the e-commerce data from tools and create a comprehensive, natural response
    that directly addresses the user's query about orders, products, or shopping.
    """

    user_query: str = dspy.InputField(desc="Original e-commerce query from user")
    ecommerce_analysis: str = dspy.OutputField(
        desc="Comprehensive, user-friendly e-commerce analysis that directly answers the query"
    )


class EcommerceToolSet(ToolSet):
    """
    A specific tool set for e-commerce and shopping tools.

    This set includes tools for order management, product search, cart operations,
    and customer support functionalities.
    """

    NAME: ClassVar[str] = "ecommerce"

    def __init__(self):
        """
        Initializes the EcommerceToolSet, defining its name, description,
        and the specific tool classes it encompasses.
        """
        from tools.ecommerce.add_to_cart import AddToCartTool
        from tools.ecommerce.get_order import GetOrderTool
        from tools.ecommerce.list_orders import ListOrdersTool
        from tools.ecommerce.return_item import ReturnItemTool
        from tools.ecommerce.search_products import SearchProductsTool
        from tools.ecommerce.track_order import TrackOrderTool

        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="E-commerce and shopping tools for order management, product search, cart operations, and customer support",
                tool_classes=[
                    GetOrderTool,
                    ListOrdersTool,
                    AddToCartTool,
                    SearchProductsTool,
                    TrackOrderTool,
                    ReturnItemTool,
                ],
            )
        )

    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Returns a predefined list of test cases for e-commerce scenarios.

        These cases cover various interactions with e-commerce tools, including
        order management, product search, cart operations, and customer support.
        """
        return [
            ToolSetTestCase(
                request="I want to check my order status for order 12345",
                expected_tools=["track_order"],
                expected_arguments={"track_order": {"order_id": "12345"}},
                description="Check specific order status",
                tool_set=cls.NAME,
                scenario="order_management",
            ),
            ToolSetTestCase(
                request="Show me all orders for customer@example.com",
                expected_tools=["list_orders"],
                expected_arguments={
                    "list_orders": {"customer_email": "customer@example.com"}
                },
                description="List customer orders",
                tool_set=cls.NAME,
                scenario="order_management",
            ),
            ToolSetTestCase(
                request="Add product SKU123 to my cart",
                expected_tools=["add_to_cart"],
                expected_arguments={"add_to_cart": {"product_sku": "SKU123"}},
                description="Add item to shopping cart",
                tool_set=cls.NAME,
                scenario="shopping",
            ),
            ToolSetTestCase(
                request="Search for wireless headphones under $100",
                expected_tools=["search_products"],
                expected_arguments={
                    "search_products": {
                        "query": "wireless headphones",
                        "max_price": 100,
                    }
                },
                description="Product search with price filter",
                tool_set=cls.NAME,
                scenario="shopping",
            ),
            ToolSetTestCase(
                request="Track my order ORD789",
                expected_tools=["track_order"],
                expected_arguments={"track_order": {"order_id": "ORD789"}},
                description="Track shipment status",
                tool_set=cls.NAME,
                scenario="order_management",
            ),
            ToolSetTestCase(
                request="Get details for order ORD123",
                expected_tools=["get_order"],
                expected_arguments={"get_order": {"order_id": "ORD123"}},
                description="Retrieve order details",
                tool_set=cls.NAME,
                scenario="order_management",
            ),
            ToolSetTestCase(
                request="Return item ITEM456 from order ORD123 because it's defective",
                expected_tools=["return_item"],
                expected_arguments={
                    "return_item": {
                        "order_id": "ORD123",
                        "item_id": "ITEM456",
                        "reason": "defective",
                    }
                },
                description="Return defective item",
                tool_set=cls.NAME,
                scenario="customer_support",
            ),
            ToolSetTestCase(
                request="I need to find laptops in my price range and add one to my cart",
                expected_tools=["search_products"],
                expected_arguments={"search_products": {"query": "laptops"}},
                description="Multi-step shopping process - search phase",
                tool_set=cls.NAME,
                scenario="shopping",
            ),
            ToolSetTestCase(
                request="Find bluetooth speakers under $50",
                expected_tools=["search_products"],
                expected_arguments={
                    "search_products": {"query": "bluetooth speakers", "max_price": 50}
                },
                description="Product search with specific category and price",
                tool_set=cls.NAME,
                scenario="shopping",
            ),
            ToolSetTestCase(
                request="Check the status of order 98765 and get full order details",
                expected_tools=["track_order", "get_order"],
                expected_arguments={},  # Multiple tools expected, hard to predict exact order
                description="Comprehensive order inquiry",
                tool_set=cls.NAME,
                scenario="order_management",
            ),
            ToolSetTestCase(
                request="List all my recent orders and track the latest one",
                expected_tools=["list_orders", "track_order"],
                expected_arguments={},  # Customer email would need to be extracted from context
                description="Recent orders with tracking follow-up",
                tool_set=cls.NAME,
                scenario="order_management",
            ),
            ToolSetTestCase(
                request="Search for gaming keyboards and add the best one under $150 to cart",
                expected_tools=["search_products", "add_to_cart"],
                expected_arguments={
                    "search_products": {"query": "gaming keyboards", "max_price": 150}
                },
                description="Product search with intent to purchase",
                tool_set=cls.NAME,
                scenario="shopping",
            ),
        ]

    @classmethod
    def get_react_signature(cls) -> Type[dspy.Signature]:
        """
        Return the React signature for e-commerce tools.

        This signature contains e-commerce operation instructions to ensure
        tools receive proper identifiers and handle shopping workflows correctly.
        """
        return EcommerceReactSignature

    @classmethod
    def get_extract_signature(cls) -> Type[dspy.Signature]:
        """
        Return the Extract signature for e-commerce synthesis.

        This signature focuses on synthesizing e-commerce information into
        user-friendly analysis without any tool-specific instructions.
        """
        return EcommerceExtractSignature
