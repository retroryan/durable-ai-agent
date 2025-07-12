"""
Simple historical weather service for demo purposes.

This would normally be a separate MCP server, but for the demo
we're creating a minimal implementation.
"""

from fastmcp import FastMCP
from datetime import datetime

# Create the historical weather service
server = FastMCP("HistoricalWeatherService")


@server.tool()
def get_historical_weather(location: str, date: str) -> str:
    """
    Get historical weather for a location on a specific date.
    
    Args:
        location: City or location name
        date: Date in YYYY-MM-DD format
    
    Returns:
        Historical weather description
    """
    # Demo implementation - returns mock data
    return f"Historical weather for {location} on {date}: High: 25°C, Low: 15°C, Clear skies"


@server.tool()
def get_climate_average(location: str, month: int) -> str:
    """
    Get climate averages for a location and month.
    
    Args:
        location: City or location name
        month: Month number (1-12)
    
    Returns:
        Climate average description
    """
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_name = month_names[month - 1] if 1 <= month <= 12 else "Unknown"
    
    return f"Climate average for {location} in {month_name}: Avg High: 20°C, Avg Low: 10°C, Rainfall: 50mm"


@server.tool()
def get_weather_records(location: str) -> str:
    """
    Get weather records for a location.
    
    Args:
        location: City or location name
    
    Returns:
        Weather records description
    """
    return f"Weather records for {location}: Highest temp: 42°C (Jan 2020), Lowest: -5°C (Jul 2018)"


if __name__ == "__main__":
    # Run as standalone server if needed
    server.run(transport="stdio")