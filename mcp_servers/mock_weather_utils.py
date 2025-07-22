"""Mock weather utilities for MCP servers.

This module provides common mock data and utilities for weather-related MCP servers
to use when running in mock mode.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


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