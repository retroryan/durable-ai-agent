from datetime import datetime, timedelta
from typing import ClassVar, Optional, Type

import requests
from pydantic import BaseModel, Field, field_validator

from shared.tool_utils.base_tool import BaseTool


class ForecastRequest(BaseModel):
    latitude: float = Field(
        ge=-90,
        le=90,
        description="REQUIRED: Latitude coordinate (-90 to 90) - extract from location names",
    )
    longitude: float = Field(
        ge=-180,
        le=180,
        description="REQUIRED: Longitude coordinate (-180 to 180) - extract from location names",
    )
    days: int = Field(
        default=7, ge=1, le=16, description="Number of forecast days (1-16)"
    )

    @field_validator("latitude", "longitude", mode="before")
    def convert_to_float(cls, v):
        if isinstance(v, str):
            v = v.strip(" \"' ")
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Cannot convert '{v}' to float")
        return v


class WeatherForecastTool(BaseTool):
    NAME: ClassVar[str] = "get_weather_forecast"
    MODULE: ClassVar[str] = "tools.precision_agriculture.weather_forecast"

    description: str = (
        "Get weather forecast for a location including temperature, precipitation, "
        "wind, and other meteorological conditions"
    )
    args_model: Type[BaseModel] = ForecastRequest

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
- 2025-01-17: High 22°C, Low 15°C, Precipitation 3.5mm"""

    def _real_call(self, latitude: float, longitude: float, days: int = 7) -> str:
        """Make real API call to get weather forecast data."""
        try:
            location_name = f"Location at {latitude:.4f}, {longitude:.4f}"

            # Call Open-Meteo API
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "forecast_days": days,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum,precipitation_hours,wind_speed_10m_max,wind_gusts_10m_max,uv_index_max",
                "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,snowfall,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
                "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
                "timezone": "auto",
            }

            response = requests.get(
                "https://api.open-meteo.com/v1/forecast", params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            # Format the response as a readable string
            current = data.get("current", {})
            daily = data.get("daily", {})

            # Build formatted output
            output = f"""Weather Forecast for {latitude:.4f}, {longitude:.4f}
Location: {location_name}
Forecast Period: {days} days

Current Conditions:
- Temperature: {current.get('temperature_2m', 'N/A')}°C
- Humidity: {current.get('relative_humidity_2m', 'N/A')}%
- Wind Speed: {current.get('wind_speed_10m', 'N/A')} km/h
- Precipitation: {current.get('precipitation', 0)} mm

Daily Forecast Summary:"""

            # Add daily forecasts
            if daily and "time" in daily:
                for i in range(min(days, len(daily["time"]))):
                    date = daily["time"][i]
                    temp_max = (
                        daily.get("temperature_2m_max", [])[i]
                        if i < len(daily.get("temperature_2m_max", []))
                        else "N/A"
                    )
                    temp_min = (
                        daily.get("temperature_2m_min", [])[i]
                        if i < len(daily.get("temperature_2m_min", []))
                        else "N/A"
                    )
                    precip = (
                        daily.get("precipitation_sum", [])[i]
                        if i < len(daily.get("precipitation_sum", []))
                        else "N/A"
                    )

                    output += f"\n- {date}: High {temp_max}°C, Low {temp_min}°C, Precipitation {precip}mm"

            return output

        except Exception as e:
            return f"Error retrieving weather forecast: {str(e)}"

    def execute(self, latitude: float, longitude: float, days: int = 7) -> str:
        if self.mock_results:
            return self._mock_results(latitude, longitude, days)
        else:
            return self._real_call(latitude, longitude, days)

    def get_test_cases(self) -> list[dict]:
        return [
            {
                "description": "Get 7-day forecast by coordinates",
                "inputs": {"latitude": 40.7128, "longitude": -74.0060, "days": 7},
            },
            {
                "description": "Get extended 16-day forecast by coordinates",
                "inputs": {"latitude": 51.5074, "longitude": -0.1278, "days": 16},
            },
            {
                "description": "Get short-term forecast (3 days)",
                "inputs": {"latitude": 25.7617, "longitude": -80.1918, "days": 3},
            },
        ]
