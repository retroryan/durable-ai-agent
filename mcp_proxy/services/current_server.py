"""
Simple current weather service for demo purposes.

This would normally be a separate MCP server, but for the demo
we're creating a minimal implementation.
"""

from fastmcp import FastMCP

# Create the current weather service
server = FastMCP("CurrentWeatherService")


@server.tool()
def get_current_weather(location: str) -> str:
    """
    Get current weather for a location.
    
    Args:
        location: City or location name
    
    Returns:
        Current weather description
    """
    # Demo implementation - returns mock data
    return f"Current weather in {location}: 22°C, Partly cloudy, Humidity: 65%"


@server.tool()
def get_temperature(location: str) -> str:
    """
    Get current temperature for a location.
    
    Args:
        location: City or location name
    
    Returns:
        Current temperature
    """
    return f"Temperature in {location}: 22°C (feels like 20°C)"


@server.tool()
def get_conditions(location: str) -> str:
    """
    Get current weather conditions.
    
    Args:
        location: City or location name
    
    Returns:
        Weather conditions description
    """
    return f"Conditions in {location}: Partly cloudy, Wind: 10 km/h NW, Visibility: 10 km"


if __name__ == "__main__":
    # Run as standalone server if needed
    server.run(transport="stdio")