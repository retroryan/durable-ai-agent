#!/usr/bin/env python3
"""
FastMCP server for OpenMeteo historical weather data.
Returns raw JSON from the Open-Meteo API for LLM interpretation.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Union

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

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

# Initialize FastMCP server
server = FastMCP(name="openmeteo-historical")
client = OpenMeteoClient()


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint for Docker health checks."""
    return JSONResponse({"status": "healthy", "service": "historical-server"})


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

        # Coordinate priority: direct coords > location name
        if request.latitude is not None and request.longitude is not None:
            coords = {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "name": request.location
                or f"{request.latitude:.4f},{request.longitude:.4f}",
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

        # Get historical data
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
    # Start the server with HTTP transport
    import os

    host = os.getenv(
        "MCP_HOST", "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1"
    )
    port = int(os.getenv("MCP_PORT", "7779"))
    print(f"Starting historical server on {host}:{port}")
    server.run(transport="streamable-http", host=host, port=port, path="/mcp")
