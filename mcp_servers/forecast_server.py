#!/usr/bin/env python3
"""
FastMCP server for OpenMeteo weather forecast tool.
Returns raw JSON from the Open-Meteo API for LLM interpretation.
"""

import json
import logging
from typing import Optional, Union
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import shared utilities
try:
    # When running as a script
    from api_utils import get_coordinates, OpenMeteoClient, get_daily_params, get_hourly_params, API_TYPE_FORECAST
    from models import ForecastRequest
except ImportError:
    # When imported as a module
    from .api_utils import get_coordinates, OpenMeteoClient, get_daily_params, get_hourly_params, API_TYPE_FORECAST
    from .models import ForecastRequest

# Initialize FastMCP server
server = FastMCP(name="openmeteo-forecast")
client = OpenMeteoClient()


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint for Docker health checks."""
    return JSONResponse({"status": "healthy", "service": "forecast-server"})


@server.tool
async def get_weather_forecast(request: ForecastRequest) -> dict:
    """Get weather forecast with coordinate optimization.
    
    Performance tip: Providing latitude/longitude is 3x faster than location name.
    Pydantic automatically handles type conversion from strings to floats.
    
    Args:
        request: ForecastRequest with location/coordinates and days
    
    Returns:
        Structured forecast data with location info, current conditions, and daily/hourly data
    """
    try:
        # Pydantic has already validated the request and converted types
        # Coordinate priority: direct coords > location name
        if request.latitude is not None and request.longitude is not None:
            coords = {
                "latitude": request.latitude, 
                "longitude": request.longitude, 
                "name": request.location or f"{request.latitude:.4f},{request.longitude:.4f}"
            }
        elif request.location:
            coords = await get_coordinates(request.location)
            if not coords:
                return {
                    "error": f"Could not find location: {request.location}. Please try a major city name."
                }
        else:
            # This should not happen due to Pydantic validation
            return {
                "error": "Either location name or coordinates (latitude, longitude) required"
            }

        # Get forecast data
        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "forecast_days": request.days,
            "daily": ",".join(get_daily_params()),
            "hourly": ",".join(get_hourly_params()),
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto"
        }
        
        data = await client.get(API_TYPE_FORECAST, params)
        
        # Add location info
        data["location_info"] = {
            "name": coords.get("name", request.location),
            "coordinates": {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"]
            }
        }
        
        # Add summary
        data["summary"] = f"Weather forecast for {coords.get('name', request.location)} ({request.days} days)"
        
        return data
        
    except Exception as e:
        return {
            "error": f"Error getting forecast: {str(e)}"
        }


if __name__ == "__main__":
    # Start the server with HTTP transport
    import os
    host = os.getenv("MCP_HOST", "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "7778"))
    print(f"Starting forecast server on {host}:{port}")
    server.run(transport="streamable-http", host=host, port=port, path="/mcp")