"""
MCP Servers for OpenMeteo Weather Data

This package provides Model Context Protocol (MCP) servers for accessing
OpenMeteo weather data with specialized functionality for different domains:

- forecast_server: Real-time and predictive weather data
- historical_server: Historical weather patterns and trends  
- agricultural_server: Farm-specific conditions and growing data

Each server operates independently and can be used with MCP-compatible clients.
"""

from .api_utils import OpenMeteoClient

__all__ = ["OpenMeteoClient"]
