from datetime import datetime, timedelta
from typing import ClassVar, List, Optional, Type

import dspy

from .base_tool_sets import ToolSet, ToolSetConfig, ToolSetTestCase


# NOTE: ReactSignatures in this project follow a specific design pattern:
# - They only define input fields (e.g., user_query)
# - The ReactAgent dynamically adds the standard React output fields at runtime:
#   (next_thought, next_tool_name, next_tool_args)
# - This separation allows tool sets to provide domain-specific instructions
#   while the ReactAgent handles the standard React pattern implementation

class AgricultureReactSignature(dspy.Signature):
    """Weather tool execution requirements with coordinate extraction.

    CURRENT DATE: {current_date}

    CRITICAL: ALWAYS extract latitude and longitude coordinates from location references.
    NEVER use location strings - weather applications require precise coordinates.

    COORDINATE EXTRACTION EXAMPLES:
    - "New York City" → latitude: 40.7128, longitude: -74.0060
    - "Des Moines, Iowa" → latitude: 41.5868, longitude: -93.6250
    - "Ames, Iowa" → latitude: 42.0308, longitude: -93.6319
    - "San Francisco" → latitude: 37.7749, longitude: -122.4194
    - "London, England" → latitude: 51.5074, longitude: -0.1278
    - "Olympia, Washington" → latitude: 47.0379, longitude: -122.9007
    - "Miami" → latitude: 25.7617, longitude: -80.1918

    WEATHER PRECISION REQUIREMENTS:
    - Local weather varies significantly by elevation and proximity to water
    - Microclimates affect temperature and precipitation patterns
    - Urban heat islands can create temperature differences
    - Coastal effects impact humidity and temperature ranges
    - Agricultural applications require precise coordinates for microclimates

    USE COORDINATES ONLY - extract from ANY location reference.
    """

    user_query: str = dspy.InputField(
        desc="Weather-related query that may reference locations by name"
    )


class AgricultureExtractSignature(dspy.Signature):
    """Synthesize weather information into user-friendly analysis.

    Take the weather data from tools and create a comprehensive, natural response
    that directly addresses the user's query.
    """

    user_query: str = dspy.InputField(desc="Original weather query from user")
    weather_analysis: str = dspy.OutputField(
        desc="Comprehensive, user-friendly weather analysis that directly answers the query"
    )


class AgricultureToolSet(ToolSet):
    """
    A specific tool set for weather-related tools.

    This set includes tools for weather forecasting, agricultural conditions,
    and historical weather data retrieval.
    """

    NAME: ClassVar[str] = "agriculture"

    def __init__(self):
        """
        Initializes the AgricultureToolSet, defining its name, description,
        and the specific tool classes it encompasses.
        """
        from tools.agriculture.agricultural_weather import (
            AgriculturalWeatherTool,
        )
        from tools.agriculture.historical_weather import HistoricalWeatherTool
        from tools.agriculture.weather_forecast import WeatherForecastTool

        super().__init__(
            config=ToolSetConfig(
                name=self.NAME,
                description="Weather forecasting, agricultural conditions, and historical weather data tools via MCP",
                tool_classes=[
                    AgriculturalWeatherTool,
                    WeatherForecastTool,
                    HistoricalWeatherTool,
                ],
            )
        )

    @classmethod
    def get_test_cases(cls) -> List[ToolSetTestCase]:
        """
        Returns a predefined list of test cases for weather scenarios.

        These cases cover various interactions with weather tools, including
        forecasting, agricultural conditions, and historical data queries.
        """
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        month_and_week_ago = (datetime.now() - timedelta(days=37)).strftime("%Y-%m-%d")

        return [
            ToolSetTestCase(
                request="What's the weather like in New York and should I bring an umbrella?",
                expected_tools=["get_weather_forecast"],
                expected_arguments={
                    "get_weather_forecast": {"latitude": 40.7128, "longitude": -74.0060}
                },
                description="Weather forecast with umbrella recommendation",
                tool_set=cls.NAME,
                scenario="forecast",
            ),
            ToolSetTestCase(
                request="What's the weather forecast for New York City?",
                expected_tools=["get_weather_forecast"],
                expected_arguments={
                    "get_weather_forecast": {"latitude": 40.7128, "longitude": -74.0060}
                },
                description="Basic weather forecast request",
                tool_set=cls.NAME,
                scenario="forecast",
            ),
            ToolSetTestCase(
                request="I need the 10-day weather forecast for London",
                expected_tools=["get_weather_forecast"],
                expected_arguments={
                    "get_weather_forecast": {
                        "latitude": 51.5074,
                        "longitude": -0.1278,
                        "days": 10,
                    }
                },
                description="Weather forecast for international city",
                tool_set=cls.NAME,
                scenario="forecast",
            ),
            ToolSetTestCase(
                request="What are the agricultural conditions in Des Moines, Iowa?",
                expected_tools=["get_agricultural_conditions"],
                expected_arguments={
                    "get_agricultural_conditions": {
                        "latitude": 41.5868,
                        "longitude": -93.6250,
                    }
                },
                description="Agricultural weather conditions",
                tool_set=cls.NAME,
                scenario="agriculture",
            ),
            ToolSetTestCase(
                request="Are conditions good for planting corn in Ames, Iowa?",
                expected_tools=["get_agricultural_conditions"],
                expected_arguments={
                    "get_agricultural_conditions": {
                        "latitude": 42.0308,
                        "longitude": -93.6319,
                        "crop_type": "corn",
                    }
                },
                description="Agricultural planning query",
                tool_set=cls.NAME,
                scenario="agriculture",
            ),
            ToolSetTestCase(
                request=f"What was the weather like in San Francisco from {month_and_week_ago} to {month_ago}?",
                expected_tools=["get_historical_weather"],
                expected_arguments={
                    "get_historical_weather": {
                        "latitude": 37.7749,
                        "longitude": -122.4194,
                        "start_date": month_and_week_ago,
                        "end_date": month_ago,
                    }
                },
                description="Historical weather data query",
                tool_set=cls.NAME,
                scenario="historical",
            ),
            ToolSetTestCase(
                request="Compare the weather in New York and Los Angeles",
                expected_tools=["get_weather_forecast"],
                expected_arguments={},  # Multiple calls expected, hard to predict order
                description="Multi-city weather comparison",
                tool_set=cls.NAME,
                scenario="comparison",
            ),
            ToolSetTestCase(
                request="What are the soil moisture levels at my tree farm in Olympia, Washington?",
                expected_tools=["get_agricultural_conditions"],
                expected_arguments={
                    "get_agricultural_conditions": {
                        "latitude": 47.0379,
                        "longitude": -122.9007,
                        "crop_type": "trees",
                    }
                },
                description="Tree farm agricultural conditions",
                tool_set=cls.NAME,
                scenario="agriculture",
            ),
            ToolSetTestCase(
                request=f"Compare the historical weather from {month_ago} with the current forecast for Miami",
                expected_tools=["get_historical_weather", "get_weather_forecast"],
                expected_arguments={},  # Multiple tools, complex to predict exact args
                description="Historical and forecast comparison",
                tool_set=cls.NAME,
                scenario="comparison",
            ),
        ]

    @classmethod
    def get_react_signature(cls) -> Type[dspy.Signature]:
        """
        Return the React signature for weather tools.

        This signature contains coordinate extraction instructions to ensure
        weather tools receive precise latitude/longitude instead of location strings.
        """
        return AgricultureReactSignature

    @classmethod
    def get_extract_signature(cls) -> Type[dspy.Signature]:
        """
        Return the Extract signature for weather synthesis.

        This signature focuses on synthesizing weather information into
        user-friendly analysis without any tool-specific instructions.
        """
        return AgricultureExtractSignature
