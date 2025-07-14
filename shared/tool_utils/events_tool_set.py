from datetime import datetime, timedelta
from typing import ClassVar, List, Optional, Type

import dspy

from .base_tool_sets import ToolSet, ToolSetConfig, ToolSetTestCase


class EventsReactSignature(dspy.Signature):
    """Event management tool execution requirements.

    CURRENT DATE: {current_date}

    EVENT MANAGEMENT GUIDELINES:
    - Always use specific dates when creating events (YYYY-MM-DD format preferred)
    - For location references, use standardized city names
    - When searching for events, be flexible with location matching

    LOCATION STANDARDIZATION:
    - "Sydney" → Sydney, Australia
    - "Auckland" → Auckland, New Zealand
    - "Melbourne" → Melbourne, Australia
    - "Brisbane" → Brisbane, Australia
    - "Perth" → Perth, Australia
    - "Adelaide" → Adelaide, Australia
    - "Wellington" → Wellington, New Zealand

    EVENT CREATION PRECISION:
    - Always include clear event titles
    - Specify exact dates and times when possible
    - Use normalized location names for consistency
    - Include meaningful descriptions for better searchability

    EVENT SEARCH FLEXIBILITY:
    - Support partial location matching
    - Allow date range searches (months, years)
    - Enable event type filtering
    - Handle location variations and abbreviations

    Use standardized formats for better event management.
    """

    user_query: str = dspy.InputField(
        desc="Event-related query that may reference locations, dates, or event types"
    )


class EventsExtractSignature(dspy.Signature):
    """Synthesize event information into user-friendly responses.

    Take the event data from tools and create a comprehensive, natural response
    that directly addresses the user's query about events.
    """

    user_query: str = dspy.InputField(desc="Original event query from user")
    event_analysis: str = dspy.OutputField(
        desc="Comprehensive, user-friendly event analysis that directly answers the query"
    )


class EventsToolSet(ToolSet):
    """
    A specific tool set for event management tools.

    This set includes tools for finding, creating, and canceling events
    across various locations and time periods.
    """

    NAME: ClassVar[str] = "events"

    def __init__(self):
        """
        Initializes the EventsToolSet, defining its name, description,
        and the specific tool classes it encompasses.
        """
        from tools.events.cancel_event import CancelEventTool
        from tools.events.create_event import CreateEventTool
        from tools.events.find_events import FindEventsTool

        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="Event management tools for finding, creating, and canceling events",
                tool_classes=[FindEventsTool, CreateEventTool, CancelEventTool],
            )
        )

    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Returns a predefined list of test cases for event management scenarios.

        These cases cover various interactions with event tools, including
        event discovery, creation, and cancellation.
        """
        return [
            ToolSetTestCase(
                request="Find all events happening in Sydney",
                expected_tools=["find_events"],
                expected_arguments={"find_events": {"location": "Sydney"}},
                description="Search for all events in a specific city",
                tool_set=cls.NAME,
                scenario="event_discovery",
            ),
            ToolSetTestCase(
                request="What events are happening in Auckland in March?",
                expected_tools=["find_events"],
                expected_arguments={
                    "find_events": {"location": "Auckland", "date": "March"}
                },
                description="Search for events by location and month",
                tool_set=cls.NAME,
                scenario="event_discovery",
            ),
            ToolSetTestCase(
                request="Find comedy festivals and events across all cities",
                expected_tools=["find_events"],
                expected_arguments={"find_events": {"event_type": "comedy"}},
                description="Search for events by type across locations",
                tool_set=cls.NAME,
                scenario="event_discovery",
            ),
            ToolSetTestCase(
                request="Show me film festivals in Melbourne",
                expected_tools=["find_events"],
                expected_arguments={
                    "find_events": {"location": "Melbourne", "event_type": "film"}
                },
                description="Find specific event type in specific location",
                tool_set=cls.NAME,
                scenario="event_discovery",
            ),
            ToolSetTestCase(
                request="What's happening in Wellington in 2025?",
                expected_tools=["find_events"],
                expected_arguments={
                    "find_events": {"location": "Wellington", "date": "2025"}
                },
                description="Search events by location and year",
                tool_set=cls.NAME,
                scenario="event_discovery",
            ),
            ToolSetTestCase(
                request="Find events in Brisbane during September",
                expected_tools=["find_events"],
                expected_arguments={
                    "find_events": {"location": "Brisbane", "date": "September"}
                },
                description="Search for events by city and specific month",
                tool_set=cls.NAME,
                scenario="event_discovery",
            ),
            ToolSetTestCase(
                request="Create a tech conference in Sydney for August 15th",
                expected_tools=["create_event"],
                expected_arguments={
                    "create_event": {
                        "title": "tech conference",
                        "location": "Sydney",
                        "date": "August 15th",
                    }
                },
                description="Create a new business event in a major city",
                tool_set=cls.NAME,
                scenario="event_creation",
            ),
            ToolSetTestCase(
                request="Schedule a music festival in Auckland for summer",
                expected_tools=["create_event"],
                expected_arguments={
                    "create_event": {
                        "title": "music festival",
                        "location": "Auckland",
                        "date": "summer",
                    }
                },
                description="Create a large-scale entertainment event",
                tool_set=cls.NAME,
                scenario="event_creation",
            ),
            ToolSetTestCase(
                request="Cancel event EVT123 because of venue issues",
                expected_tools=["cancel_event"],
                expected_arguments={
                    "cancel_event": {"event_id": "EVT123", "reason": "venue issues"}
                },
                description="Cancel event with specific reason",
                tool_set=cls.NAME,
                scenario="event_cancellation",
            ),
            ToolSetTestCase(
                request="I want to find arts festivals in Adelaide and create a similar event in Perth",
                expected_tools=["find_events", "create_event"],
                expected_arguments={},  # Multiple tools expected, hard to predict order
                description="Research existing events to plan new one",
                tool_set=cls.NAME,
                scenario="event_management",
            ),
            ToolSetTestCase(
                request="Cancel my booking RES789 and help me find alternative events in Melbourne",
                expected_tools=["cancel_event", "find_events"],
                expected_arguments={},  # Multiple tools, complex to predict exact args
                description="Cancel and find replacement events",
                tool_set=cls.NAME,
                scenario="event_management",
            ),
            ToolSetTestCase(
                request="Show me what festivals are happening in March across Australia and New Zealand",
                expected_tools=["find_events"],
                expected_arguments={
                    "find_events": {"date": "March", "event_type": "festival"}
                },
                description="Broad search across regions by month and type",
                tool_set=cls.NAME,
                scenario="event_discovery",
            ),
        ]

    @classmethod
    def get_react_signature(cls) -> Type[dspy.Signature]:
        """
        Return the React signature for event tools.

        This signature contains event management instructions to ensure
        events tools receive proper formatting and location normalization.
        """
        return EventsReactSignature

    @classmethod
    def get_extract_signature(cls) -> Type[dspy.Signature]:
        """
        Return the Extract signature for event synthesis.

        This signature focuses on synthesizing event information into
        user-friendly analysis without any tool-specific instructions.
        """
        return EventsExtractSignature
