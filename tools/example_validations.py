"""
Examples of how to use the common validation pattern in different tools
"""
from datetime import datetime
from typing import Any, Dict

from .validators import (
    FieldType,
    FieldValidator,
    optional_string,
    required_date,
    required_email,
    required_string,
    validate_args,
)


def find_events_validated(args: Dict[str, Any]) -> Dict[str, Any]:
    """Example: find_events with validation"""
    # Define validation rules
    validators = [
        optional_string("city"),
        FieldValidator(
            "month",
            FieldType.STRING,
            required=True,
            custom_validator=lambda m: m.capitalize()
            in [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
            error_message="Invalid month. Please provide a valid month name (e.g., 'January')",
        ),
    ]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    # Now use validated values with confidence
    search_city = validated["city"].lower()
    search_month = validated["month"].capitalize()

    # ... rest of the implementation


def book_pto_validated(args: Dict[str, Any]) -> Dict[str, Any]:
    """Example: book_pto with validation"""
    # Define validation rules with custom validators
    validators = [
        required_email("email"),
        required_date("start_date"),
        required_date("end_date"),
    ]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    # Additional business logic validation
    if validated["end_date"] < validated["start_date"]:
        return {"error": "End date must be after start date"}

    # Now use validated values
    email = validated["email"]
    start_date = validated["start_date"]
    end_date = validated["end_date"]

    # ... rest of the implementation


def get_account_balance_validated(args: Dict[str, Any]) -> Dict[str, Any]:
    """Example: account balance with enum validation"""
    validators = [
        FieldValidator(
            "account_id",
            FieldType.STRING,
            required=True,
            min_length=5,
            max_length=20,
            error_message="Account ID must be between 5 and 20 characters",
        ),
        FieldValidator(
            "account_type",
            FieldType.ENUM,
            required=False,
            default="checking",
            allowed_values=["checking", "savings", "investment"],
            error_message="Account type must be 'checking', 'savings', or 'investment'",
        ),
    ]

    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    # ... rest of the implementation


def search_products_validated(args: Dict[str, Any]) -> Dict[str, Any]:
    """Example: search with numeric constraints"""
    validators = [
        optional_string("query"),
        FieldValidator(
            "min_price",
            FieldType.FLOAT,
            required=False,
            default=0.0,
            min_value=0.0,
            error_message="Minimum price must be non-negative",
        ),
        FieldValidator(
            "max_price",
            FieldType.FLOAT,
            required=False,
            default=999999.99,
            min_value=0.0,
            error_message="Maximum price must be non-negative",
        ),
        FieldValidator(
            "limit",
            FieldType.INTEGER,
            required=False,
            default=10,
            min_value=1,
            max_value=100,
            error_message="Limit must be between 1 and 100",
        ),
    ]

    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    # Additional validation
    if validated["max_price"] < validated["min_price"]:
        return {"error": "Maximum price must be greater than minimum price"}

    # ... rest of the implementation
