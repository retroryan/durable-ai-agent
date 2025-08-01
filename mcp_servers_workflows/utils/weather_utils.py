"""
Weather data implementation utilities.
All the logic, none of the server boilerplate.
"""

import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field

from models.mcp_models import ForecastRequest, HistoricalRequest, AgriculturalRequest


# Mock data models
class MockCoordinates(BaseModel):
    """Model for mock coordinate data."""
    latitude: float
    longitude: float
    name: str


class LocationInfo(BaseModel):
    """Model for location information in responses."""
    name: str
    coordinates: Dict[str, float]


class DailyWeatherData(BaseModel):
    """Model for daily weather data."""
    time: List[str]
    temperature_2m_max: List[float]
    temperature_2m_min: List[float]
    precipitation_sum: List[float]
    wind_speed_10m_max: Optional[List[float]] = None
    rain_sum: Optional[List[float]] = None
    soil_moisture_0_to_10cm: Optional[List[float]] = None
    soil_moisture_10_to_30cm: Optional[List[float]] = None
    evapotranspiration: Optional[List[float]] = None


class CurrentWeatherData(BaseModel):
    """Model for current weather conditions."""
    temperature_2m: float
    relative_humidity_2m: float
    precipitation: float
    weather_code: int
    wind_speed_10m: Optional[float] = None


class AgriculturalMetrics(BaseModel):
    """Model for agricultural metrics."""
    average_soil_moisture: float
    growing_degree_days: float
    precipitation_total: float


class CropSpecific(BaseModel):
    """Model for crop-specific data."""
    crop_type: str
    water_stress_index: float
    growth_stage: str
    irrigation_recommendation: str


class MockWeatherResponse(BaseModel):
    """Base model for mock weather responses."""
    location_info: LocationInfo
    daily: DailyWeatherData
    summary: str
    mock: bool = True
    current: Optional[CurrentWeatherData] = None
    agricultural_metrics: Optional[AgriculturalMetrics] = None
    crop_specific: Optional[CropSpecific] = None


# Common mock coordinates for major locations
MOCK_COORDINATES: Dict[str, MockCoordinates] = {
    "new york": MockCoordinates(latitude=40.7128, longitude=-74.0060, name="New York"),
    "london": MockCoordinates(latitude=51.5074, longitude=-0.1278, name="London"),
    "san francisco": MockCoordinates(latitude=37.7749, longitude=-122.4194, name="San Francisco"),
    "des moines": MockCoordinates(latitude=41.5868, longitude=-93.6250, name="Des Moines"),
    "ames": MockCoordinates(latitude=42.0308, longitude=-93.6319, name="Ames"),
    "miami": MockCoordinates(latitude=25.7617, longitude=-80.1918, name="Miami"),
    "olympia": MockCoordinates(latitude=47.0379, longitude=-122.9007, name="Olympia"),
}

# Default coordinates to use when location not found
DEFAULT_COORDINATES = MockCoordinates(latitude=40.7128, longitude=-74.0060, name="Unknown Location")


def is_mock_mode() -> bool:
    """Check if the server is running in mock mode."""
    return os.getenv("TOOLS_MOCK", "false").lower() == "true"


def normalize_location_key(location: str) -> str:
    """Normalize a location string for lookup in mock coordinates."""
    return location.lower().replace(",", "").strip()


def resolve_coordinates(
    location: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float]
) -> Optional[MockCoordinates]:
    """Resolve coordinates from either lat/lon or location name in mock mode.
    
    Args:
        location: Optional location name
        latitude: Optional latitude
        longitude: Optional longitude
        
    Returns:
        MockCoordinates object, or None if no valid input
    """
    if latitude is not None and longitude is not None:
        return MockCoordinates(
            latitude=latitude,
            longitude=longitude,
            name=location or f"{latitude:.4f},{longitude:.4f}"
        )
    elif location:
        location_key = normalize_location_key(location)
        mock_coord = MOCK_COORDINATES.get(location_key)
        if mock_coord:
            return mock_coord
        else:
            # Return default with the provided location name
            return MockCoordinates(
                latitude=DEFAULT_COORDINATES.latitude,
                longitude=DEFAULT_COORDINATES.longitude,
                name=location
            )
    else:
        return None


def create_location_info(coords: MockCoordinates) -> LocationInfo:
    """Create a standardized location_info structure.
    
    Args:
        coords: MockCoordinates object
        
    Returns:
        LocationInfo object
    """
    return LocationInfo(
        name=coords.name,
        coordinates={
            "latitude": coords.latitude,
            "longitude": coords.longitude,
        }
    )


from .api_client import (
    API_TYPE_FORECAST,
    API_TYPE_ARCHIVE,
    OpenMeteoClient,
    get_coordinates,
    get_daily_params,
    get_hourly_params,
)

# Single client instance
client = OpenMeteoClient()

# Check if we're in mock mode using existing utility
MOCK_MODE = is_mock_mode()


async def get_forecast_data(request: ForecastRequest) -> dict:
    """Get weather forecast data."""
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
                return {
                    "error": "Either location name or coordinates (latitude, longitude) required"
                }

        # Return mock data if in mock mode
        if MOCK_MODE:
            return _get_mock_forecast(coords, request.days)

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


async def get_historical_data(request: HistoricalRequest) -> dict:
    """Get historical weather data."""
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
                return {
                    "error": "Either location name or coordinates (latitude, longitude) required"
                }

        # Return mock data if in mock mode
        if MOCK_MODE:
            return _get_mock_historical(coords, request.start_date, request.end_date)

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


async def get_agricultural_data(request: AgriculturalRequest) -> dict:
    """Get agricultural weather conditions."""
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
            return _get_mock_agricultural(coords, request.days, None)

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


# Mock data generation functions
def _get_mock_forecast(coords: MockCoordinates, days: int) -> dict:
    """Return mock forecast data for testing."""
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


def _get_mock_historical(coords: MockCoordinates, start_date: str, end_date: str) -> dict:
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


def _get_mock_agricultural(coords: MockCoordinates, days: int, crop_type: Optional[str]) -> dict:
    """Return mock agricultural weather data for testing."""
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