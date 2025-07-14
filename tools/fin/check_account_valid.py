import json
from pathlib import Path
from typing import Any, Dict

from ..validators import FieldType, FieldValidator, optional_string, validate_args


# this is made to demonstrate functionality but it could just as durably be an API call
# called as part of a temporal activity with automatic retries
def check_account_valid(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define validation rules - at least one of email or account_id is required
    validators = [
        FieldValidator("email", FieldType.EMAIL, required=False, default=""),
        optional_string("account_id"),
    ]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    email = validated["email"]
    account_id = validated["account_id"]

    # Ensure at least one identifier is provided
    if not email and not account_id:
        return {"error": "Either email or account_id must be provided"}

    file_path = (
        Path(__file__).resolve().parent.parent / "data" / "customer_account_data.json"
    )
    if not file_path.exists():
        return {"error": "Data file not found."}

    with open(file_path, "r") as file:
        data = json.load(file)
    account_list = data["accounts"]

    for account in account_list:
        if (email and account["email"] == email) or (
            account_id and account["account_id"] == account_id
        ):
            return {"status": "account valid"}

    return_msg = (
        "Account not found with email address "
        + email
        + " or account ID: "
        + account_id
    )
    return {"error": return_msg}
