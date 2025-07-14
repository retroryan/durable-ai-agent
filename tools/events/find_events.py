import json
import os
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Optional, Type

from pydantic import BaseModel, Field

from shared.tool_utils.base_tool import BaseTool


class EventSearchRequest(BaseModel):
    location: Optional[str] = Field(
        default=None, description="City or venue where events are taking place"
    )
    date: Optional[str] = Field(
        default=None,
        description="Date or date range for events (e.g., 'today', '2024-07-15', 'this weekend')",
    )
    event_type: Optional[str] = Field(
        default=None, description="Type of event (concert, sports, conference, etc.)"
    )


class FindEventsTool(BaseTool):
    NAME: ClassVar[str] = "find_events"
    MODULE: ClassVar[str] = "tools.events.find_events"

    description: str = (
        "Find events based on location, date, or type including concerts, "
        "sports events, conferences, and other local activities"
    )
    args_model: Type[BaseModel] = EventSearchRequest

    def _load_events_data(self) -> dict:
        """Load events data from find_events_data.json"""
        try:
            # Get the path to the data file
            current_dir = Path(__file__).parent
            data_file = current_dir.parent / "data" / "find_events_data.json"

            with open(data_file, "r") as f:
                return json.load(f)
        except Exception as e:
            # Return empty dict if file can't be loaded
            return {}

    def _filter_events_by_date(self, events: list, date_filter: str) -> list:
        """Filter events by date criteria"""
        if not date_filter:
            return events

        # Parse common date formats
        date_filter_lower = date_filter.lower()
        current_date = datetime.now()

        filtered_events = []

        for event in events:
            event_date_from = datetime.fromisoformat(event["dateFrom"])
            event_date_to = (
                datetime.fromisoformat(event["dateTo"])
                if event.get("dateTo")
                else event_date_from
            )

            # Check various date criteria
            if date_filter_lower in ["march", "mar"]:
                if event_date_from.month == 3 or event_date_to.month == 3:
                    filtered_events.append(event)
            elif date_filter_lower in ["january", "jan"]:
                if event_date_from.month == 1 or event_date_to.month == 1:
                    filtered_events.append(event)
            elif date_filter_lower in ["february", "feb"]:
                if event_date_from.month == 2 or event_date_to.month == 2:
                    filtered_events.append(event)
            elif date_filter_lower in ["april", "apr"]:
                if event_date_from.month == 4 or event_date_to.month == 4:
                    filtered_events.append(event)
            elif date_filter_lower in ["may"]:
                if event_date_from.month == 5 or event_date_to.month == 5:
                    filtered_events.append(event)
            elif date_filter_lower in ["june", "jun"]:
                if event_date_from.month == 6 or event_date_to.month == 6:
                    filtered_events.append(event)
            elif date_filter_lower in ["july", "jul"]:
                if event_date_from.month == 7 or event_date_to.month == 7:
                    filtered_events.append(event)
            elif date_filter_lower in ["august", "aug"]:
                if event_date_from.month == 8 or event_date_to.month == 8:
                    filtered_events.append(event)
            elif date_filter_lower in ["september", "sep"]:
                if event_date_from.month == 9 or event_date_to.month == 9:
                    filtered_events.append(event)
            elif date_filter_lower in ["october", "oct"]:
                if event_date_from.month == 10 or event_date_to.month == 10:
                    filtered_events.append(event)
            elif date_filter_lower in ["november", "nov"]:
                if event_date_from.month == 11 or event_date_to.month == 11:
                    filtered_events.append(event)
            elif date_filter_lower in ["december", "dec"]:
                if event_date_from.month == 12 or event_date_to.month == 12:
                    filtered_events.append(event)
            elif "2025" in date_filter_lower:
                if event_date_from.year == 2025 or event_date_to.year == 2025:
                    filtered_events.append(event)
            elif date_filter in event["dateFrom"] or (
                event.get("dateTo") and date_filter in event["dateTo"]
            ):
                filtered_events.append(event)
            else:
                # Try exact date match or partial match
                try:
                    search_date = datetime.fromisoformat(date_filter)
                    if event_date_from <= search_date <= event_date_to:
                        filtered_events.append(event)
                except:
                    # If parsing fails, include event for broad search
                    filtered_events.append(event)

        return filtered_events

    def _normalize_location(self, location: str) -> str:
        """Normalize location name for searching"""
        if not location:
            return ""

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
            "new zealand": "Wellington",
        }

        return location_mapping.get(location_lower, location.title())

    def execute(
        self,
        location: Optional[str] = None,
        date: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> dict:
        try:
            # Load events data from JSON file
            events_data = self._load_events_data()

            if not events_data:
                return {"error": "Could not load events data"}

            # Build search criteria
            criteria = []
            if location:
                criteria.append(f"in {location}")
            if date:
                criteria.append(f"on {date}")
            if event_type:
                criteria.append(f"type: {event_type}")

            criteria_str = " ".join(criteria) if criteria else "matching your criteria"

            # Search events by location
            matching_events = []

            if location:
                # Normalize the location for searching
                normalized_location = self._normalize_location(location)

                # Search in the specific location
                if normalized_location in events_data:
                    location_events = events_data[normalized_location]

                    # Filter by date if specified
                    if date:
                        location_events = self._filter_events_by_date(
                            location_events, date
                        )

                    # Convert to expected format and add location info
                    for event in location_events:
                        formatted_event = {
                            "id": f"EVT_{normalized_location}_{hash(event['eventName']) % 10000}",
                            "title": event["eventName"],
                            "date_from": event["dateFrom"],
                            "date_to": event.get("dateTo", event["dateFrom"]),
                            "location": normalized_location,
                            "description": event["description"],
                            "url": event.get("url", ""),
                        }

                        # Filter by event type if specified
                        if event_type:
                            event_desc_lower = event["description"].lower()
                            event_name_lower = event["eventName"].lower()
                            if (
                                event_type.lower() in event_desc_lower
                                or event_type.lower() in event_name_lower
                            ):
                                matching_events.append(formatted_event)
                        else:
                            matching_events.append(formatted_event)

                else:
                    # Search across all locations for partial matches
                    for city, city_events in events_data.items():
                        if location.lower() in city.lower():
                            for event in city_events:
                                formatted_event = {
                                    "id": f"EVT_{city}_{hash(event['eventName']) % 10000}",
                                    "title": event["eventName"],
                                    "date_from": event["dateFrom"],
                                    "date_to": event.get("dateTo", event["dateFrom"]),
                                    "location": city,
                                    "description": event["description"],
                                    "url": event.get("url", ""),
                                }
                                matching_events.append(formatted_event)
            else:
                # No location specified, search all events
                for city, city_events in events_data.items():
                    city_events_filtered = city_events

                    # Filter by date if specified
                    if date:
                        city_events_filtered = self._filter_events_by_date(
                            city_events_filtered, date
                        )

                    for event in city_events_filtered:
                        formatted_event = {
                            "id": f"EVT_{city}_{hash(event['eventName']) % 10000}",
                            "title": event["eventName"],
                            "date_from": event["dateFrom"],
                            "date_to": event.get("dateTo", event["dateFrom"]),
                            "location": city,
                            "description": event["description"],
                            "url": event.get("url", ""),
                        }

                        # Filter by event type if specified
                        if event_type:
                            event_desc_lower = event["description"].lower()
                            event_name_lower = event["eventName"].lower()
                            if (
                                event_type.lower() in event_desc_lower
                                or event_type.lower() in event_name_lower
                            ):
                                matching_events.append(formatted_event)
                        else:
                            matching_events.append(formatted_event)

            return {
                "events": matching_events,
                "count": len(matching_events),
                "search_criteria": {
                    "location": location,
                    "date": date,
                    "event_type": event_type,
                },
                "summary": f"Found {len(matching_events)} events {criteria_str}",
                "available_locations": list(events_data.keys())
                if not location
                else None,
            }

        except Exception as e:
            return {"error": f"Error searching for events: {str(e)}"}

    def get_test_cases(self) -> list[dict]:
        return [
            {
                "description": "Find all events in Sydney",
                "inputs": {"location": "Sydney"},
            },
            {
                "description": "Find events in Auckland in March",
                "inputs": {"location": "Auckland", "date": "March"},
            },
            {
                "description": "Find comedy events across all locations",
                "inputs": {"event_type": "comedy"},
            },
            {
                "description": "Find film festivals in Melbourne",
                "inputs": {"location": "Melbourne", "event_type": "film"},
            },
            {
                "description": "Find all events in Wellington",
                "inputs": {"location": "Wellington"},
            },
            {
                "description": "Find events in Brisbane in September",
                "inputs": {"location": "Brisbane", "date": "September"},
            },
        ]
