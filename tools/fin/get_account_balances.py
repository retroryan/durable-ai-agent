import json
from pathlib import Path
from typing import Any, Dict

from ..validators import required_string, validate_args


# this is made to demonstrate functionality but it could just as durably be an API call
# this assumes it's a valid account - use check_account_valid() to verify that first
def get_account_balance(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define validation rules
    validators = [
        required_string(
            "email_address_or_account_ID",
            error_message="Please provide an email address or account ID",
        )
    ]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    account_key = validated["email_address_or_account_ID"]

    file_path = (
        Path(__file__).resolve().parent.parent / "data" / "customer_account_data.json"
    )
    if not file_path.exists():
        return {"error": "Data file not found."}

    with open(file_path, "r") as file:
        data = json.load(file)
    account_list = data["accounts"]

    for account in account_list:
        if account["email"] == account_key or account["account_id"] == account_key:
            return {
                "name": account["name"],
                "email": account["email"],
                "account_id": account["account_id"],
                "checking_balance": account["checking_balance"],
                "savings_balance": account["savings_balance"],
                "bitcoin_balance": account["bitcoin_balance"],
                "account_creation_date": account["account_creation_date"],
            }

    return_msg = "Account not found with for " + account_key
    return {"error": return_msg}
