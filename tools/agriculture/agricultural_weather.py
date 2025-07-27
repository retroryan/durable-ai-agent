import os
from datetime import datetime, timedelta
from typing import ClassVar, Optional, Type

import requests
from pydantic import BaseModel

from models.types import MCPConfig
from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool

# Import the shared Pydantic model
from models.mcp_models import AgriculturalRequest


class AgriculturalWeatherTool(MCPTool):
    NAME: ClassVar[str] = "get_agricultural_conditions"
    MODULE: ClassVar[str] = "tools.agriculture.agricultural_weather"
    is_mcp: ClassVar[bool] = True

    description: str = (
        "Get agricultural weather conditions including soil moisture, evapotranspiration, "
        "and growing conditions for a location"
    )
    args_model: Type[BaseModel] = AgriculturalRequest

    # Note: get_mcp_config() is inherited from MCPTool base class

    def execute(
        self,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        days: int = 7,
        crop_type: Optional[str] = None,
    ) -> str:
        # Only used in mock mode for testing
        if self.mock_results:
            # For mock results, prefer coordinates if available
            if latitude is not None and longitude is not None:
                return self._mock_results(latitude, longitude, days, crop_type)
            elif location:
                # Mock geocoding for common locations
                coords = self._mock_geocode(location)
                return self._mock_results(coords[0], coords[1], days, crop_type)
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

    def _mock_results(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        crop_type: Optional[str] = None,
    ) -> str:
        """Return simple mock agricultural weather data."""
        location_name = f"Agricultural location at {latitude:.4f}, {longitude:.4f}"
        if crop_type:
            location_name += f" ({crop_type} farming)"
            
        return f"""Agricultural Conditions for {latitude:.4f}, {longitude:.4f}
Location: {location_name}
Forecast Period: {days} days

Current Soil Conditions:
- Surface (0-1cm): 25.5% moisture
- Shallow (1-3cm): 28.2% moisture
- Root Zone (3-9cm): 32.1% moisture
- Deep (9-27cm): 35.8% moisture

Growing Conditions:
- Evapotranspiration: 3.2mm/day
- Soil Temperature (10cm): 18.5°C
- Growing Degree Days: 12.5

Forecast Summary:
- Next 3 days: Favorable conditions for planting
- Precipitation expected: Day 4-5
- Frost risk: Low"""

    def get_test_cases(self) -> list[dict]:
        return [
            {
                "description": "Get agricultural conditions by location name",
                "inputs": {"location": "Des Moines, IA", "days": 5},
            },
            {
                "description": "Get agricultural conditions by coordinates",
                "inputs": {"latitude": 41.5868, "longitude": -93.6250, "days": 7},
            },
            {
                "description": "Get minimal forecast (1 day)",
                "inputs": {"location": "Salinas, CA", "days": 1},
            },
        ]