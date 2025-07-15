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

# Check for mock mode
MOCK_MODE = os.getenv("TOOLS_MOCK", "false").lower() == "true"
if MOCK_MODE:
    logger.info("🔧 Running agricultural server in MOCK MODE - no external API calls will be made")

# Import shared utilities
try:
    # When running as a script
    from api_utils import API_TYPE_FORECAST, OpenMeteoClient, get_coordinates

    from models import AgriculturalRequest
except ImportError:
    # When imported as a module
    from .api_utils import API_TYPE_FORECAST, OpenMeteoClient, get_coordinates
    from .models import AgriculturalRequest

# Initialize FastMCP server
server = FastMCP(name="openmeteo-agricultural")
client = OpenMeteoClient()


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Simple health check endpoint for Docker health checks."""
    return JSONResponse({"status": "healthy", "service": "agricultural-server"})


def get_mock_agricultural(coords: dict, days: int, crop_type: Optional[str]) -> dict:
    """Return mock agricultural weather data for testing."""
    from datetime import datetime, timedelta
    
    base_date = datetime.now()
    daily_data = {
        "time": [],
        "soil_moisture_0_to_10cm": [],
        "soil_moisture_10_to_30cm": [],
        "evapotranspiration": [],
        "precipitation_sum": [],
    }
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        daily_data["time"].append(date.strftime("%Y-%m-%d"))
        daily_data["soil_moisture_0_to_10cm"].append(25.5 + i * 0.2)
        daily_data["soil_moisture_10_to_30cm"].append(28.3 + i * 0.15)
        daily_data["evapotranspiration"].append(3.2 + i * 0.1)
        daily_data["precipitation_sum"].append(0 if i % 3 else 4.5)
    
    result = {
        "location_info": {
            "name": coords.get("name", f"{coords['latitude']:.4f},{coords['longitude']:.4f}"),
            "coordinates": {
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
            },
        },
        "daily": daily_data,
        "agricultural_metrics": {
            "average_soil_moisture": 26.9,
            "growing_degree_days": 125.5,
            "precipitation_total": sum(daily_data["precipitation_sum"]),
        },
        "summary": f"Mock agricultural conditions for {coords.get('name')} ({days} days)",
        "mock": True,
    }
    
    if crop_type:
        result["crop_specific"] = {
            "crop_type": crop_type,
            "water_stress_index": 0.15,
            "growth_stage": "vegetative",
            "irrigation_recommendation": "No irrigation needed"
        }
    
    return result


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
                    "olympia": {"latitude": 47.0379, "longitude": -122.9007, "name": "Olympia"},
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
                        "error": f"Could not find location: {request.location}. Please try a major city or farm name."
                    }
        else:
            # This should not happen due to Pydantic validation
            return {
                "error": "Either location name or coordinates (latitude, longitude) required"
            }

        # Return mock data if in mock mode
        if MOCK_MODE:
            return get_mock_agricultural(coords, request.days, request.crop_type)

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
    # Start the server with HTTP transport
    import os

    host = os.getenv(
        "MCP_HOST", "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1"
    )
    port = int(os.getenv("MCP_PORT", "7780"))
    print(f"Starting agricultural server on {host}:{port}")
    server.run(transport="streamable-http", host=host, port=port, path="/mcp")
