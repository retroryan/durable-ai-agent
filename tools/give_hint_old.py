from typing import Any, Dict

from .validators import optional_int, validate_args


def give_hint(args: Dict[str, Any]) -> Dict[str, str]:
    """
    Give a hint about the treasure location.
    Uses common validation pattern.
    """
    # Define validation rules
    validators = [optional_int("hint_total", default=0, min_value=0)]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    hint_total = validated["hint_total"]

    hints = [
        "The treasure is in a city known for its coffee and rain.",
        "It's located near a famous public market.",
        "The address is on a street named after a US President's wife.",
    ]

    if hint_total < len(hints):
        return {"hint": hints[hint_total]}
    else:
        return {"hint": "No more hints available."}
