import os
from datetime import datetime, timedelta
from typing import ClassVar, Optional, Type

import requests
from pydantic import BaseModel, Field, field_validator

from models.types import MCPConfig
from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool


class ForecastRequest(BaseModel):
    location: Optional[str] = Field(
        None,
        description="Location name (e.g., 'Chicago, IL'). Slower due to geocoding.",
    )
    latitude: Optional[float] = Field(
        None, 
        ge=-90,
        le=90,
        description="Direct latitude (-90 to 90). PREFERRED for faster response."
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Direct longitude (-180 to 180). PREFERRED for faster response."
    )
    days: int = Field(
        default=7, ge=1, le=16, description="Number of forecast days (1-16)"
    )

    @field_validator("latitude", "longitude", mode="before")
    def convert_to_float(cls, v):
        if v is not None and isinstance(v, str):
            v = v.strip(" \"' ")
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Cannot convert '{v}' to float")
        return v
    
    @field_validator("latitude", "longitude")
    def validate_coords(cls, v, field):
        if v is not None:
            if field.field_name == "latitude" and not -90 <= v <= 90:
                raise ValueError(f"Latitude must be between -90 and 90, got {v}")
            elif field.field_name == "longitude" and not -180 <= v <= 180:
                raise ValueError(f"Longitude must be between -180 and 180, got {v}")
        return v


class WeatherForecastTool(MCPTool):
    NAME: ClassVar[str] = "get_weather_forecast"
    MODULE: ClassVar[str] = "tools.precision_agriculture.weather_forecast"
    is_mcp: ClassVar[bool] = True

    description: str = (
        "Get weather forecast for a location including temperature, precipitation, "
        "wind, and other meteorological conditions"
    )
    args_model: Type[BaseModel] = ForecastRequest

    # MCP configuration
    # mcp_server_name identifies which MCP server this tool connects to
    # This is used to construct the prefixed tool name when using the proxy
    mcp_server_name: str = "forecast"
    
    # Note: get_mcp_config() is inherited from MCPTool base class
    # It handles dynamic tool name resolution based on MCP_USE_PROXY

    def execute(self, location: Optional[str] = None, latitude: Optional[float] = None, 
                longitude: Optional[float] = None, days: int = 7) -> str:
        # Only used in mock mode for testing
        if self.mock_results:
            # For mock results, prefer coordinates if available
            if latitude is not None and longitude is not None:
                return self._mock_results(latitude, longitude, days)
            elif location:
                # Mock geocoding for common locations
                coords = self._mock_geocode(location)
                return self._mock_results(coords[0], coords[1], days)
            else:
                raise ValueError("Either location or coordinates required")
        else:
            # Real execution happens via MCP in ToolExecutionActivity
            raise RuntimeError("MCP tools should be executed via activity")
    
    def _mock_geocode(self, location: str) -> tuple[float, float]:
        """Mock geocoding for common locations."""
        mock_coords = {
            "new york": (40.7128, -74.0060),
            "chicago": (41.8781, -87.6298),
            "los angeles": (34.0522, -118.2437),
            "sydney": (-33.8688, 151.2093),
            "melbourne": (-37.8136, 144.9631),
        }
        location_lower = location.lower()
        for key, coords in mock_coords.items():
            if key in location_lower:
                return coords
        # Default to NYC if not found
        return (40.7128, -74.0060)

    def _mock_results(self, latitude: float, longitude: float, days: int = 7) -> str:
        """Return simple mock weather forecast data."""
        return f"""Weather Forecast for {latitude:.4f}, {longitude:.4f}
Location: Location at {latitude:.4f}, {longitude:.4f}
Forecast Period: {days} days

Current Conditions:
- Temperature: 20°C
- Humidity: 65%
- Wind Speed: 10 km/h
- Precipitation: 0 mm

Daily Forecast Summary:
- 2025-01-15: High 23°C, Low 16°C, Precipitation 0mm
- 2025-01-16: High 24°C, Low 17°C, Precipitation 1.2mm
- 2025-01-17: High 22°C, Low 15°C, Precipitation 0.5mm"""

    def get_test_cases(self) -> list[dict]:
        return [
            {
                "description": "Get weather forecast by location name",
                "inputs": {"location": "New York, NY", "days": 7},
            },
            {
                "description": "Get weather forecast by coordinates",
                "inputs": {"latitude": 40.7128, "longitude": -74.0060, "days": 14},
            },
            {
                "description": "Get short-term forecast (3 days)",
                "inputs": {"location": "San Francisco, CA", "days": 3},
            },
        ]