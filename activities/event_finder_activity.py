"""Simple activity that calls the find_events tool."""
import json
from datetime import datetime
from typing import Any, Dict

from temporalio import activity

from tools import find_events


@activity.defn
async def find_events_activity(
    user_message: str, user_name: str = "anonymous"
) -> Dict[str, Any]:
    """
    Activity that calls find_events with hardcoded parameters.

    Args:
        user_message: The user's message (not used in current implementation)
        user_name: The name of the user making the request

    Returns:
        Dictionary with message, event_count
    """
    # For demo, always search Melbourne in current month
    city = "Melbourne"
    current_month = datetime.now().strftime("%B")

    # Get activity info for context
    info = activity.info()
    workflow_id = info.workflow_id

    # Log the activity execution with user context
    activity.logger.info(
        f"User '{user_name}' (workflow: {workflow_id}) searching for events in {city} for {current_month}"
    )

    try:
        # Call the find_events tool with dictionary argument
        args = {"city": city, "month": current_month}
        result = find_events(args)

        # Result is already a dictionary, no need to parse JSON
        events_data = result
        event_count = len(events_data.get("events", []))

        # Format personalized response message
        # Extract just the base name without the timestamp suffix
        display_name = (
            user_name.split("_")[0] + "_" + user_name.split("_")[1]
            if "_" in user_name
            else user_name
        )

        if event_count > 0:
            message = f"Hey {display_name}! I found {event_count} exciting events in {city} for {current_month}"
            first_event = events_data["events"][0]
            message += f". The first one is '{first_event['eventName']}'"
            if "dateFrom" in first_event:
                message += f" starting on {first_event['dateFrom']}"
            message += ". Would you like to hear about more events?"
        else:
            message = f"Sorry {display_name}, I couldn't find any events in {city} for {current_month}. Try checking back later or searching for a different month!"

        return {
            "message": message,
            "event_count": event_count,
        }

    except Exception as e:
        activity.logger.error(f"Error finding events: {e}")
        # Extract display name for error message too
        display_name = (
            user_name.split("_")[0] + "_" + user_name.split("_")[1]
            if "_" in user_name
            else user_name
        )
        return {
            "message": f"Sorry {display_name}, I encountered an error while searching for events: {str(e)}",
            "event_count": 0,
        }
