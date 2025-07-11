"""Utility functions for Open-Meteo data handling."""

from .date_utils import (
    get_current_date,
    get_forecast_range,
    get_historical_range,
    format_date_for_api
)

from .display import (
    Colors,
    print_colored,
    print_section_header,
    print_subsection,
    print_weather_summary,
    print_soil_conditions,
    print_precipitation_summary,
    print_location_results,
    format_api_error,
    print_attribution
)

__all__ = [
    # Date utilities
    "get_current_date",
    "get_forecast_range",
    "get_historical_range",
    "format_date_for_api",
    # Display utilities
    "Colors",
    "print_colored",
    "print_section_header",
    "print_subsection",
    "print_weather_summary",
    "print_soil_conditions",
    "print_precipitation_summary",
    "print_location_results",
    "format_api_error",
    "print_attribution"
]