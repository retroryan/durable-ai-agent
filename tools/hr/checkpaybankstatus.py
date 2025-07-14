from typing import Any, Dict

from ..validators import required_email, validate_args


def checkpaybankstatus(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define validation rules
    validators = [required_email("email")]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    email = validated["email"]

    if email == "grinch@grinch.com":
        print("THE GRINCH IS FOUND!")
        return {"status": "no money for the grinch"}

    # could do logic here or look up data but for now everyone but the grinch is getting paid
    return_msg = "connected"
    return {"status": return_msg}
