#!/usr/bin/env python3
"""
FastMCP server for agricultural weather conditions.
Returns raw JSON from the Open-Meteo API for LLM interpretation.
"""

import os
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
    from api_utils import API_TYPE_FORECAST, OpenMeteoClient, get_coordinates
    from models import AgriculturalRequest
    from mock_weather_utils import (
        is_mock_mode, resolve_coordinates, create_location_info,
        MockCoordinates, MockWeatherResponse, DailyWeatherData,
        AgriculturalMetrics, CropSpecific
    )
except ImportError:
    # When imported as a module
    from .api_utils import API_TYPE_FORECAST, OpenMeteoClient, get_coordinates
    from .models import AgriculturalRequest
    from .mock_weather_utils import (
        is_mock_mode, resolve_coordinates, create_location_info,
        MockCoordinates, MockWeatherResponse, DailyWeatherData,
        AgriculturalMetrics, CropSpecific
    )

# Check for mock mode
MOCK_MODE = is_mock_mode()
if MOCK_MODE:
    logger.info("🔧 Running agricultural server in MOCK MODE - no external API calls will be made")

# Initialize FastMCP server
server = FastMCP(name="openmeteo-agricultural")
client = OpenMeteoClient()


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint for Docker health checks."""
    return JSONResponse({"status": "healthy", "service": "agricultural-server"})


def get_mock_agricultural(coords: MockCoordinates, days: int, crop_type: Optional[str]) -> dict:
    """Return mock agricultural weather data for testing."""
    from datetime import datetime, timedelta
    
    base_date = datetime.now()
    time_list = []
    soil_moisture_0_to_10cm = []
    soil_moisture_10_to_30cm = []
    evapotranspiration = []
    precipitation_sum = []
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        time_list.append(date.strftime("%Y-%m-%d"))
        soil_moisture_0_to_10cm.append(25.5 + i * 0.2)
        soil_moisture_10_to_30cm.append(28.3 + i * 0.15)
        evapotranspiration.append(3.2 + i * 0.1)
        precipitation_sum.append(0 if i % 3 else 4.5)
    
    daily_data = DailyWeatherData(
        time=time_list,
        temperature_2m_max=[],  # Not used in agricultural
        temperature_2m_min=[],  # Not used in agricultural
        precipitation_sum=precipitation_sum,
        soil_moisture_0_to_10cm=soil_moisture_0_to_10cm,
        soil_moisture_10_to_30cm=soil_moisture_10_to_30cm,
        evapotranspiration=evapotranspiration
    )
    
    agricultural_metrics = AgriculturalMetrics(
        average_soil_moisture=26.9,
        growing_degree_days=125.5,
        precipitation_total=sum(precipitation_sum)
    )
    
    response = MockWeatherResponse(
        location_info=create_location_info(coords),
        daily=daily_data,
        agricultural_metrics=agricultural_metrics,
        summary=f"Mock agricultural conditions for {coords.name} ({days} days)",
        mock=True
    )
    
    if crop_type:
        response.crop_specific = CropSpecific(
            crop_type=crop_type,
            water_stress_index=0.15,
            growth_stage="vegetative",
            irrigation_recommendation="No irrigation needed"
        )
    
    return response.model_dump()


@server.tool
async def get_agricultural_conditions(request: AgriculturalRequest) -> dict:
    """Get agricultural conditions with coordinate optimization.

    Performance tip: Providing latitude/longitude is 3x faster than location name.
    Pydantic automatically handles type conversion from strings to floats.

    Args:
        request: AgriculturalRequest with location/coordinates and days

    Returns:
        Structured agricultural data with soil moisture, evapotranspiration, and growing conditions
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
                        "error": f"Could not find location: {request.location}. Please try a major city or farm name."
                    }
            else:
                return {
                    "error": "Either location name or coordinates (latitude, longitude) required"
                }

        # Return mock data if in mock mode
        if MOCK_MODE:
            return get_mock_agricultural(coords, request.days, None)

        # Get real agricultural data with soil and ET parameters
        params = {
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "forecast_days": request.days,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration,vapor_pressure_deficit_max",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,soil_temperature_0cm,soil_temperature_6cm,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm",
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
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
        ] = f"Agricultural conditions for {coords.get('name', request.location)} ({request.days} days) - Focus: Soil moisture, evapotranspiration, and growing conditions"

        return data

    except Exception as e:
        return {"error": f"Error getting agricultural conditions: {str(e)}"}


if __name__ == "__main__":
    import argparse
    import os

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="FastMCP Agricultural Server")
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
        port = int(os.getenv("MCP_PORT", "7780"))
        print(f"Starting agricultural server on {host}:{port}")
        server.run(transport="streamable-http", host=host, port=port, path="/mcp")
