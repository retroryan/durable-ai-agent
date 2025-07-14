from datetime import datetime, timedelta
from typing import ClassVar, Optional, Type

import requests
from pydantic import BaseModel, Field, field_validator

from shared.tool_utils.base_tool import BaseTool


class AgriculturalRequest(BaseModel):
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
        default=7, ge=1, le=7, description="Number of forecast days (1-7)"
    )
    crop_type: Optional[str] = Field(
        default=None, description="Type of crop for specialized agricultural conditions"
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


class AgriculturalWeatherTool(BaseTool):
    NAME: ClassVar[str] = "get_agricultural_conditions"
    MODULE: ClassVar[str] = "tools.precision_agriculture.agricultural_weather"

    description: str = (
        "Get agricultural weather conditions including soil moisture, evapotranspiration, "
        "and growing conditions for a location"
    )
    args_model: Type[BaseModel] = AgriculturalRequest

    def execute(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        crop_type: Optional[str] = None,
    ) -> str:
        try:
            location_name = f"Agricultural location at {latitude:.4f}, {longitude:.4f}"
            if crop_type:
                location_name += f" ({crop_type} farming)"

            # Call Open-Meteo API with agricultural parameters
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "forecast_days": days,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration,vapor_pressure_deficit_max",
                "hourly": "temperature_2m,relative_humidity_2m,precipitation,soil_temperature_0cm,soil_temperature_6cm,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm",
                "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
                "timezone": "auto",
            }

            response = requests.get(
                "https://api.open-meteo.com/v1/forecast", params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            # Format the response as a readable string
            current_hourly = data.get("hourly", {})
            daily = data.get("daily", {})

            # Get latest soil moisture values
            soil_moisture_0_1 = current_hourly.get("soil_moisture_0_to_1cm", [])
            soil_moisture_1_3 = current_hourly.get("soil_moisture_1_to_3cm", [])
            soil_moisture_3_9 = current_hourly.get("soil_moisture_3_to_9cm", [])
            soil_moisture_9_27 = current_hourly.get("soil_moisture_9_to_27cm", [])

            # Build formatted output
            output = f"""Agricultural Conditions for {latitude:.4f}, {longitude:.4f}
Location: {location_name}
Forecast Period: {days} days

Current Soil Conditions:"""

            if soil_moisture_0_1:
                output += f"\n- Surface (0-1cm): {soil_moisture_0_1[0]:.1f}% moisture"
            if soil_moisture_1_3:
                output += f"\n- Shallow (1-3cm): {soil_moisture_1_3[0]:.1f}% moisture"
            if soil_moisture_3_9:
                output += f"\n- Root Zone (3-9cm): {soil_moisture_3_9[0]:.1f}% moisture"
            if soil_moisture_9_27:
                output += f"\n- Deep (9-27cm): {soil_moisture_9_27[0]:.1f}% moisture"

            output += "\n\nDaily Agricultural Summary:"

            # Add daily agricultural data
            if daily and "time" in daily:
                et0_data = daily.get("et0_fao_evapotranspiration", [])
                vpd_data = daily.get("vapor_pressure_deficit_max", [])

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
                    et0 = et0_data[i] if i < len(et0_data) else "N/A"
                    vpd = vpd_data[i] if i < len(vpd_data) else "N/A"

                    output += f"\n- {date}:"
                    output += f"\n  Temperature: {temp_max}/{temp_min}°C"
                    output += f"\n  Precipitation: {precip}mm"
                    output += f"\n  Evapotranspiration: {et0}mm"
                    output += f"\n  Vapor Pressure Deficit: {vpd}kPa"

            if crop_type:
                output += f"\n\nCrop-Specific Notes for {crop_type}:"
                output += (
                    f"\n- Monitor soil moisture levels for optimal growing conditions"
                )
                output += f"\n- Adjust irrigation based on evapotranspiration rates"

            return output

        except Exception as e:
            return f"Error retrieving agricultural conditions: {str(e)}"

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
