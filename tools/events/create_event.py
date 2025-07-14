import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Type

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool


class EventCreationRequest(BaseModel):
    title: str = Field(..., description="Title or name of the event")
    date: str = Field(
        ...,
        description="Date and time for the event (e.g., '2024-07-20 15:00', 'tomorrow at 3pm')",
    )
    location: str = Field(..., description="Location where the event will take place")
    description: str = Field(
        default="", description="Optional description of the event"
    )


class CreateEventTool(BaseTool):
    NAME: ClassVar[str] = "create_event"
    MODULE: ClassVar[str] = "tools.events.create_event"

    description: str = (
        "Create a new event or appointment with specified title, date, "
        "location, and optional description"
    )
    args_model: Type[BaseModel] = EventCreationRequest

    def _normalize_location(self, location: str) -> str:
        """Normalize location name for storage"""
        location_lower = location.lower()

        # Map common variations to standard city names
        location_mapping = {
            "syd": "Sydney",
            "sydney": "Sydney",
            "auckland": "Auckland",
            "auck": "Auckland",
            "melbourne": "Melbourne",
            "mel": "Melbourne",
            "melb": "Melbourne",
            "brisbane": "Brisbane",
            "bris": "Brisbane",
            "perth": "Perth",
            "adelaide": "Adelaide",
            "adel": "Adelaide",
            "wellington": "Wellington",
            "welly": "Wellington",
            "wellington nz": "Wellington",
        }

        return location_mapping.get(location_lower, location.title())

    def execute(
        self, title: str, date: str, location: str, description: str = ""
    ) -> dict:
        try:
            # Generate a unique event ID
            event_id = f"EVT{random.randint(1000, 9999)}"

            # Normalize the location
            normalized_location = self._normalize_location(location)

            # Parse and validate the date (simplified)
            current_time = datetime.now()

            # For demonstration purposes, we'll just return success
            # In a real implementation, you'd save this to the JSON file
            return {
                "event_id": event_id,
                "status": "created",
                "title": title,
                "date": date,
                "location": normalized_location,
                "description": description or "No description provided",
                "created_at": current_time.isoformat(),
                "confirmation": f"Successfully created event '{title}' for {date} in {normalized_location}",
                "note": "Event would be stored in the location-based structure for future searches",
            }

        except Exception as e:
            return {"error": f"Error creating event: {str(e)}"}

    def get_test_cases(self) -> list[dict]:
        return [
            {
                "description": "Create a business meeting in Sydney",
                "inputs": {
                    "title": "Team Meeting",
                    "date": "2025-07-20 14:00",
                    "location": "Sydney",
                    "description": "Weekly team sync meeting",
                },
            },
            {
                "description": "Schedule a social event in Auckland",
                "inputs": {
                    "title": "Birthday Party",
                    "date": "2025-07-25 18:00",
                    "location": "Auckland",
                },
            },
            {
                "description": "Create a conference event in Melbourne",
                "inputs": {
                    "title": "Tech Summit 2025",
                    "date": "2025-08-15 09:00",
                    "location": "Melbourne",
                    "description": "Annual technology conference with industry leaders",
                },
            },
            {
                "description": "Create an event in Wellington",
                "inputs": {
                    "title": "Art Exhibition Opening",
                    "date": "2025-09-10 19:00",
                    "location": "Wellington",
                    "description": "Contemporary art exhibition opening night",
                },
            },
        ]
