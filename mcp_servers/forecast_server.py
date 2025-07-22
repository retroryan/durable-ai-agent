#!/usr/bin/env python3
"""
FastMCP server for OpenMeteo weather forecast tool.
Returns raw JSON from the Open-Meteo API for LLM interpretation.
"""

import json
import logging
import os
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
    from api_utils import (
        API_TYPE_FORECAST,
        OpenMeteoClient,
        get_coordinates,
        get_daily_params,
        get_hourly_params,
    )
    from models import ForecastRequest
    from mock_weather_utils import (
        is_mock_mode, resolve_coordinates, create_location_info,
        MockCoordinates, MockWeatherResponse, DailyWeatherData, CurrentWeatherData
    )
except ImportError:
    # When imported as a module
    from .api_utils import (
        API_TYPE_FORECAST,
        OpenMeteoClient,
        get_coordinates,
        get_daily_params,
        get_hourly_params,
    )
    from .models import ForecastRequest
    from .mock_weather_utils import (
        is_mock_mode, resolve_coordinates, create_location_info,
        MockCoordinates, MockWeatherResponse, DailyWeatherData, CurrentWeatherData
    )

# Check for mock mode
MOCK_MODE = is_mock_mode()
if MOCK_MODE:
    logger.info("🔧 Running forecast server in MOCK MODE - no external API calls will be made")

# Initialize FastMCP server
server = FastMCP(name="openmeteo-forecast")
client = OpenMeteoClient()


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint for Docker health checks."""
    return JSONResponse({"status": "healthy", "service": "forecast-server"})


def get_mock_forecast(coords: MockCoordinates, days: int) -> dict:
    """Return mock forecast data for testing."""
    from datetime import datetime, timedelta
    
    base_date = datetime.now()
    time_list = []
    temperature_2m_max = []
    temperature_2m_min = []
    precipitation_sum = []
    wind_speed_10m_max = []
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        time_list.append(date.strftime("%Y-%m-%d"))
        temperature_2m_max.append(20 + i * 0.5)
        temperature_2m_min.append(10 + i * 0.3)
        precipitation_sum.append(0 if i % 3 else 2.5)
        wind_speed_10m_max.append(15 + i * 0.2)
    
    daily_data = DailyWeatherData(
        time=time_list,
        temperature_2m_max=temperature_2m_max,
        temperature_2m_min=temperature_2m_min,
        precipitation_sum=precipitation_sum,
        wind_speed_10m_max=wind_speed_10m_max
    )
    
    current_weather = CurrentWeatherData(
        temperature_2m=18.5,
        relative_humidity_2m=65,
        precipitation=0,
        weather_code=0,
        wind_speed_10m=12.5
    )
    
    response = MockWeatherResponse(
        location_info=create_location_info(coords),
        current=current_weather,
        daily=daily_data,
        summary=f"Mock weather forecast for {coords.name} ({days} days)",
        mock=True
    )
    
    return response.model_dump()


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
        # In mock mode, use mock utilities for coordinate resolution
        if MOCK_MODE:
            coords = resolve_coordinates(request.location, request.latitude, request.longitude)
            if not coords:
                return {
                    "error": "Either location name or coordinates (latitude, longitude) required"
                }
        else:
            # Real mode: use API or provided coordinates
            if request.latitude is not None and request.longitude is not None:
                coords = {
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "name": request.location or f"{request.latitude:.4f},{request.longitude:.4f}",
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

        # Return mock data if in mock mode
        if MOCK_MODE:
            return get_mock_forecast(coords, request.days)

        # Get real forecast data
        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "forecast_days": request.days,
            "daily": ",".join(get_daily_params()),
            "hourly": ",".join(get_hourly_params()),
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        }

        data = await client.get(API_TYPE_FORECAST, params)

        # Add location info
        data["location_info"] = {
            "name": coords.get("name", request.location),
            "coordinates": {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
            },
        }

        # Add summary
        data[
            "summary"
        ] = f"Weather forecast for {coords.get('name', request.location)} ({request.days} days)"

        return data

    except Exception as e:
        return {"error": f"Error getting forecast: {str(e)}"}


if __name__ == "__main__":
    import argparse
    import os

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="FastMCP Weather Forecast Server")
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "http", "sse", "streamable-http"],
        default="streamable-http",
        help="Transport protocol to use (default: streamable-http)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv(
            "MCP_HOST", "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1"
        ),
        help="Host to bind to (for HTTP transports)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "7778")),
        help="Port to bind to (for HTTP transports)",
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="URL path for HTTP transports (default: /mcp)",
    )
    args = parser.parse_args()

    # Run the server with appropriate transport
    if args.transport == "stdio":
        # For stdio, we don't need host/port
        server.run(transport="stdio")
    else:
        # For HTTP transports, include host/port/path
        print(f"Starting forecast server on {args.host}:{args.port}{args.path}")
        server.run(
            transport=args.transport,
            host=args.host,
            port=args.port,
            path=args.path,
        )
