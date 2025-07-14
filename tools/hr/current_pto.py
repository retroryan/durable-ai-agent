import json
from pathlib import Path
from typing import Any, Dict

from ..validators import required_email, validate_args


def current_pto(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define validation rules
    validators = [required_email("email")]

    # Validate arguments
    validated = validate_args(args, validators)
    if "error" in validated:
        return validated

    email = validated["email"]

    file_path = (
        Path(__file__).resolve().parent.parent / "data" / "employee_pto_data.json"
    )
    if not file_path.exists():
        return {"error": "Data file not found."}

    data = json.load(open(file_path))
    employee_list = data["theCompany"]["employees"]

    for employee in employee_list:
        if employee["email"] == email:
            num_hours = int(employee["currentPTOHrs"])
            num_days = float(num_hours / 8)
            return {
                "num_hours": num_hours,
                "num_days": num_days,
            }

    return_msg = "Employee not found with email address " + email
    return {"error": return_msg}
