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

# Check for mock mode
MOCK_MODE = os.getenv("TOOLS_MOCK", "false").lower() == "true"
if MOCK_MODE:
    logger.info("🔧 Running forecast server in MOCK MODE - no external API calls will be made")

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

# Initialize FastMCP server
server = FastMCP(name="openmeteo-forecast")
client = OpenMeteoClient()


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint for Docker health checks."""
    return JSONResponse({"status": "healthy", "service": "forecast-server"})


def get_mock_forecast(coords: dict, days: int) -> dict:
    """Return mock forecast data for testing."""
    from datetime import datetime, timedelta
    
    base_date = datetime.now()
    daily_data = {
        "time": [],
        "temperature_2m_max": [],
        "temperature_2m_min": [],
        "precipitation_sum": [],
        "wind_speed_10m_max": [],
    }
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        daily_data["time"].append(date.strftime("%Y-%m-%d"))
        daily_data["temperature_2m_max"].append(20 + i * 0.5)
        daily_data["temperature_2m_min"].append(10 + i * 0.3)
        daily_data["precipitation_sum"].append(0 if i % 3 else 2.5)
        daily_data["wind_speed_10m_max"].append(15 + i * 0.2)
    
    return {
        "location_info": {
            "name": coords.get("name", f"{coords['latitude']:.4f},{coords['longitude']:.4f}"),
            "coordinates": {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
            },
        },
        "current": {
            "temperature_2m": 18.5,
            "relative_humidity_2m": 65,
            "precipitation": 0,
            "weather_code": 0,
            "wind_speed_10m": 12.5,
        },
        "daily": daily_data,
        "summary": f"Mock weather forecast for {coords.get('name')} ({days} days)",
        "mock": True,
    }


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
                "name": request.location
                or f"{request.latitude:.4f},{request.longitude:.4f}",
            }
        elif request.location:
            # In mock mode, use simple coordinate mapping
            if MOCK_MODE:
                # Simple mock coordinates for common locations
                mock_coords = {
                    "new york": {"latitude": 40.7128, "longitude": -74.0060, "name": "New York"},
                    "london": {"latitude": 51.5074, "longitude": -0.1278, "name": "London"},
                    "san francisco": {"latitude": 37.7749, "longitude": -122.4194, "name": "San Francisco"},
                    "des moines": {"latitude": 41.5868, "longitude": -93.6250, "name": "Des Moines"},
                    "ames": {"latitude": 42.0308, "longitude": -93.6319, "name": "Ames"},
                    "miami": {"latitude": 25.7617, "longitude": -80.1918, "name": "Miami"},
                }
                location_key = request.location.lower().replace(",", "").strip()
                coords = mock_coords.get(location_key, {
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "name": request.location
                })
            else:
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
