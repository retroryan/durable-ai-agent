"""
Simple forecast weather service for demo purposes.

This would normally be a separate MCP server, but for the demo
we're creating a minimal implementation.
"""

from fastmcp import FastMCP

# Create the forecast service
server = FastMCP("ForecastWeatherService")


@server.tool()
def get_forecast(location: str, days: int = 5) -> str:
    """
    Get weather forecast for a location.

    Args:
        location: City or location name
        days: Number of days to forecast (default: 5)

    Returns:
        Weather forecast description
    """
    # Demo implementation - returns mock data
    return f"Forecast for {location} ({days} days): Partly cloudy with temperatures 15-25°C"


@server.tool()
def get_hourly_forecast(location: str, hours: int = 24) -> str:
    """
    Get hourly weather forecast.

    Args:
        location: City or location name
        hours: Number of hours to forecast (default: 24)

    Returns:
        Hourly forecast description
    """
    return f"Hourly forecast for {location} ({hours}h): Variable conditions, 20% chance of rain"


if __name__ == "__main__":
    # Run as standalone server if needed
    server.run(transport="stdio")
