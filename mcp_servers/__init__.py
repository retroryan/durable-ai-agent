"""
MCP Servers for OpenMeteo Weather Data

This package provides a unified Model Context Protocol (MCP) server for accessing
OpenMeteo weather data with three specialized tools:

- get_weather_forecast: Real-time and predictive weather data
- get_historical_weather: Historical weather patterns and trends  
- get_agricultural_conditions: Farm-specific conditions and growing data

All tools are exposed through a single server running on port 7778.
"""

from .utils.api_client import OpenMeteoClient

__all__ = ["OpenMeteoClient"]
