"""Set reminder tool implementation using the unified base class."""
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Type

from pydantic import BaseModel, Field, field_validator

from shared.tool_utils.base_tool import BaseTool, ToolTestCase


class SetReminderTool(BaseTool):
    """Tool for setting reminders."""

    NAME: ClassVar[str] = "set_reminder"
    MODULE: ClassVar[str] = "tools.productivity.set_reminder"

    class Arguments(BaseModel):
        """Argument validation model."""

        message: str = Field(
            ..., min_length=1, max_length=500, description="The reminder message"
        )
        time: str = Field(
            ..., description="When to remind (e.g., '2pm', 'tomorrow', 'in 30 minutes')"
        )

        @field_validator("time")
        @classmethod
        def validate_time(cls, v: str) -> str:
            """Basic validation that time is not empty."""
            if not v.strip():
                raise ValueError("Time cannot be empty")
            return v.strip()

    # Tool definition as instance attributes
    description: str = "Set a reminder for a specific time"
    args_model: Type[BaseModel] = Arguments

    def execute(self, message: str, time: str) -> Dict[str, Any]:
        """Execute the tool to set a reminder."""
        # In a real implementation, this would schedule the reminder
        # For now, we'll just return a confirmation
        return {
            "status": "success",
            "message": f"Reminder set: '{message}' at {time}",
            "reminder_id": f"rem_{datetime.now().timestamp():.0f}",
        }

    @classmethod
    def get_test_cases(cls) -> List[ToolTestCase]:
        """Return test cases for this tool."""
        return [
            ToolTestCase(
                request="Remind me to call mom at 3pm",
                expected_tools=["set_reminder"],
                description="Basic reminder with time",
            ),
            ToolTestCase(
                request="Set a reminder for tomorrow to buy groceries",
                expected_tools=["set_reminder"],
                description="Future reminder",
            ),
            ToolTestCase(
                request="I need a reminder in 30 minutes to check the oven",
                expected_tools=["set_reminder"],
                description="Relative time reminder",
            ),
            ToolTestCase(
                request="Don't let me forget the meeting at 2pm",
                expected_tools=["set_reminder"],
                description="Alternative phrasing",
            ),
        ]
