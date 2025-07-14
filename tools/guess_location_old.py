from typing import Any, Dict

from .validators import optional_string, validate_args


def guess_location(args: Dict[str, Any]) -> Dict[str, str]:
    """Guess the treasure location."""
    # Define validation rules
    validators = [
        optional_string("address"),
        optional_string("city"),
        optional_string("state"),
    ]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    address = validated["address"]
    city = validated["city"]
    state = validated["state"]

    if "seattle" in city.lower() and "lenora" in address.lower():
        return {"status": "Correct!", "message": "You found the treasure!"}
    else:
        return {
            "status": "Incorrect",
            "message": "Sorry, that's not the right location.",
        }
