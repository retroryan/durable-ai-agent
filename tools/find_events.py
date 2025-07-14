import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .validators import FieldType, FieldValidator, optional_string, validate_args


def find_events(args: Dict[str, Any]) -> Dict[str, Any]:
    # Define validation rules
    validators = [
        optional_string("city"),
        FieldValidator(
            "month",
            FieldType.STRING,
            required=False,
            default="",
            custom_validator=lambda m: not m
            or m.capitalize()
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

    search_city = validated["city"].lower()
    search_month = validated["month"].capitalize()

    file_path = Path(__file__).resolve().parent / "data" / "find_events_data.json"
    if not file_path.exists():
        return {"error": "Data file not found."}

    if search_month:
        month_number = datetime.strptime(search_month, "%B").month
    else:
        return {"error": "Month is required."}

    # Helper to wrap months into [1..12]
    def get_adjacent_months(m):
        prev_m = 12 if m == 1 else (m - 1)
        next_m = 1 if m == 12 else (m + 1)
        return [prev_m, m, next_m]

    valid_months = get_adjacent_months(month_number)

    matching_events = []
    for city_name, events in json.load(open(file_path)).items():
        if search_city and search_city not in city_name.lower():
            continue

        for event in events:
            date_from = datetime.strptime(event["dateFrom"], "%Y-%m-%d")
            date_to = datetime.strptime(event["dateTo"], "%Y-%m-%d")

            # If the event's start or end month is in our valid months
            if date_from.month in valid_months or date_to.month in valid_months:
                # Add metadata explaining how it matches
                if date_from.month == month_number or date_to.month == month_number:
                    month_context = "requested month"
                elif (
                    date_from.month == valid_months[0]
                    or date_to.month == valid_months[0]
                ):
                    month_context = "previous month"
                else:
                    month_context = "next month"

                matching_events.append(
                    {
                        "city": city_name,
                        "eventName": event["eventName"],
                        "dateFrom": event["dateFrom"],
                        "dateTo": event["dateTo"],
                        "description": event["description"],
                        "month": month_context,
                    }
                )

    # Add top-level metadata if you wish
    return {
        "note": f"Returning events from {search_month} plus one month either side (i.e., {', '.join(datetime(2025, m, 1).strftime('%B') for m in valid_months)}).",
        "events": matching_events,
    }
