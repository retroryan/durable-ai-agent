from typing import Any, Dict

from ..validators import required_date, required_email, validate_args


def book_pto(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define validation rules
    validators = [
        required_email("email"),
        required_date("start_date"),
        required_date("end_date"),
    ]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    email = validated["email"]
    start_date = validated["start_date"]
    end_date = validated["end_date"]

    # Additional business logic validation
    if end_date < start_date:
        return {"error": "End date must be after or equal to start date"}

    print(
        f"[BookPTO] Totally would send an email confirmation of PTO from {start_date} to {end_date} to {email} here!"
    )

    return {"status": "success"}
