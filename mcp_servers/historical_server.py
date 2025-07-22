#!/usr/bin/env python3
"""
FastMCP server for OpenMeteo historical weather data.
Returns raw JSON from the Open-Meteo API for LLM interpretation.
"""

import os
import logging
from datetime import date, datetime, timedelta
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
        API_TYPE_ARCHIVE,
        OpenMeteoClient,
        get_coordinates,
        get_daily_params,
        get_hourly_params,
    )
    from models import HistoricalRequest
    from mock_weather_utils import (
        is_mock_mode, resolve_coordinates, create_location_info,
        MockCoordinates, MockWeatherResponse, DailyWeatherData
    )
except ImportError:
    # When imported as a module
    from .api_utils import (
        API_TYPE_ARCHIVE,
        OpenMeteoClient,
        get_coordinates,
        get_daily_params,
        get_hourly_params,
    )
    from .models import HistoricalRequest
    from .mock_weather_utils import (
        is_mock_mode, resolve_coordinates, create_location_info,
        MockCoordinates, MockWeatherResponse, DailyWeatherData
    )

# Check for mock mode
MOCK_MODE = is_mock_mode()
if MOCK_MODE:
    logger.info("🔧 Running historical server in MOCK MODE - no external API calls will be made")

# Initialize FastMCP server
server = FastMCP(name="openmeteo-historical")
client = OpenMeteoClient()


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint for Docker health checks."""
    return JSONResponse({"status": "healthy", "service": "historical-server"})


def get_mock_historical(coords: MockCoordinates, start_date: str, end_date: str) -> dict:
    """Return mock historical weather data for testing."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end - start).days + 1
    
    time_list = []
    temperature_2m_max = []
    temperature_2m_min = []
    precipitation_sum = []
    rain_sum = []
    
    for i in range(days):
        date_str = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        time_list.append(date_str)
        temperature_2m_max.append(22 + i * 0.3)
        temperature_2m_min.append(12 + i * 0.2)
        precipitation_sum.append(0 if i % 4 else 5.2)
        rain_sum.append(0 if i % 4 else 5.2)
    
    daily_data = DailyWeatherData(
        time=time_list,
        temperature_2m_max=temperature_2m_max,
        temperature_2m_min=temperature_2m_min,
        precipitation_sum=precipitation_sum,
        rain_sum=rain_sum
    )
    
    response = MockWeatherResponse(
        location_info=create_location_info(coords),
        daily=daily_data,
        summary=f"Mock historical weather from {start_date} to {end_date}",
        mock=True
    )
    
    return response.model_dump()


@server.tool
async def get_historical_weather(request: HistoricalRequest) -> dict:
    """Get historical weather with coordinate optimization.

    Performance tip: Providing latitude/longitude is 3x faster than location name.
    Pydantic automatically handles type conversion and date validation.

    Args:
        request: HistoricalRequest with dates and location/coordinates

    Returns:
        Structured historical weather data with daily aggregates
    """
    try:
        # Pydantic has already validated dates and coordinates
        start = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(request.end_date, "%Y-%m-%d").date()

        # Additional validation for historical data availability
        min_date = date.today() - timedelta(days=5)
        if end > min_date:
            return {
                "error": f"Historical data only available before {min_date}. Use forecast API for recent dates."
            }

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
            return get_mock_historical(coords, request.start_date, request.end_date)

        # Get real historical data
        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": ",".join(get_daily_params()),
            "timezone": "auto",
        }

        data = await client.get(API_TYPE_ARCHIVE, params)

        # Add location info
        data["location_info"] = {
            "name": coords.get(
                "name",
                request.location or f"{coords['latitude']},{coords['longitude']}",
            ),
            "coordinates": {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
            },
        }

        # Add summary
        data[
            "summary"
        ] = f"Historical weather for {coords.get('name', request.location)} from {request.start_date} to {request.end_date}"

        return data

    except Exception as e:
        return {"error": f"Error getting historical data: {str(e)}"}


if __name__ == "__main__":
    import argparse
    import os

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="FastMCP Historical Weather Server")
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "streamable-http"],
        default="streamable-http",
        help="Transport protocol (stdio or streamable-http)"
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        # Run in stdio mode for direct process communication
        server.run(transport="stdio")
    else:
        # Run in HTTP mode
        host = os.getenv(
            "MCP_HOST", "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1"
        )
        port = int(os.getenv("MCP_PORT", "7779"))
        print(f"Starting historical server on {host}:{port}")
        server.run(transport="streamable-http", host=host, port=port, path="/mcp")
