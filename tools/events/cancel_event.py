from datetime import datetime
from typing import ClassVar, Optional, Type

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool


class EventCancellationRequest(BaseModel):
    event_id: str = Field(
        ..., description="Unique identifier of the event or reservation to cancel"
    )
    reason: Optional[str] = Field(
        default=None, description="Optional reason for cancellation"
    )
    notify_attendees: bool = Field(
        default=True, description="Whether to notify attendees of the cancellation"
    )


class CancelEventTool(BaseTool):
    NAME: ClassVar[str] = "cancel_event"
    MODULE: ClassVar[str] = "tools.events.cancel_event"

    description: str = (
        "Cancel an existing event or reservation by event ID, "
        "with optional reason and attendee notification"
    )
    args_model: Type[BaseModel] = EventCancellationRequest

    def execute(
        self, event_id: str, reason: Optional[str] = None, notify_attendees: bool = True
    ) -> dict:
        try:
            # Mock event lookup
            event_exists = event_id.startswith(("EVT", "RES", "APT"))

            if not event_exists:
                return {"error": f"Event not found: {event_id}"}

            current_time = datetime.now()

            return {
                "status": "cancelled",
                "event_id": event_id,
                "reason": reason or "No reason provided",
                "cancelled_at": current_time.isoformat(),
                "attendees_notified": notify_attendees,
                "confirmation": f"Event {event_id} has been successfully cancelled",
                "refund_status": "Processing refund if applicable",
            }

        except Exception as e:
            return {"error": f"Error cancelling event: {str(e)}"}

    def get_test_cases(self) -> list[dict]:
        return [
            {
                "description": "Cancel event with weather reason",
                "inputs": {
                    "event_id": "EVT1234",
                    "reason": "Severe weather conditions",
                    "notify_attendees": True,
                },
            },
            {
                "description": "Cancel reservation without reason",
                "inputs": {"event_id": "RES5678", "notify_attendees": False},
            },
            {
                "description": "Cancel appointment with detailed reason",
                "inputs": {
                    "event_id": "APT9012",
                    "reason": "Schedule conflict - rescheduling required",
                    "notify_attendees": True,
                },
            },
        ]
