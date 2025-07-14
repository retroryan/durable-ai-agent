from datetime import datetime, timedelta
from typing import ClassVar, Optional, Type

import requests
from pydantic import BaseModel, Field, field_validator

from shared.tool_utils.base_tool import BaseTool


class HistoricalRequest(BaseModel):
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
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

    @field_validator("latitude", "longitude", mode="before")
    def convert_to_float(cls, v):
        if isinstance(v, str):
            v = v.strip(" \"' ")
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Cannot convert '{v}' to float")
        return v

    @field_validator("start_date", "end_date")
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")
        return v

    @field_validator("end_date")
    def validate_date_range(cls, v, info):
        if "start_date" in info.data:
            start_date = datetime.strptime(info.data["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(v, "%Y-%m-%d")

            if end_date < start_date:
                raise ValueError("End date must be after start date")

            min_historical_date = datetime.now() - timedelta(days=5)
            if end_date > min_historical_date:
                raise ValueError(
                    f"Historical data only available for dates at least 5 days in the past. Latest available date: {min_historical_date.strftime('%Y-%m-%d')}"
                )

        return v


class HistoricalWeatherTool(BaseTool):
    NAME: ClassVar[str] = "get_historical_weather"
    MODULE: ClassVar[str] = "tools.precision_agriculture.historical_weather"

    description: str = (
        "Get historical weather data for a location and date range. "
        "Only works for dates at least 5 days in the past."
    )
    args_model: Type[BaseModel] = HistoricalRequest

    def _mock_results(self, latitude: float, longitude: float, start_date: str, end_date: str) -> str:
        """Return simple mock historical weather data."""
        return f"""Historical Weather Data for {latitude:.4f}, {longitude:.4f}
Location: Location at {latitude:.4f}, {longitude:.4f}
Period: {start_date} to {end_date}

Daily Historical Summary:

{start_date}:
- Temperature: High 22°C, Low 15°C
- Precipitation: 2.5mm
- Max Wind Speed: 15 km/h
- Max UV Index: 6

Period Summary:
- Average High: 22.0°C
- Average Low: 15.0°C
- Total Precipitation: 2.5mm"""

    def _real_call(self, latitude: float, longitude: float, start_date: str, end_date: str) -> str:
        """Make real API call to get historical weather data."""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            min_historical_date = datetime.now() - timedelta(days=5)
            if end_dt > min_historical_date:
                return f"Error: Historical data only available for dates at least 5 days in the past. Latest available date: {min_historical_date.strftime('%Y-%m-%d')}"

            location_name = f"Location at {latitude:.4f}, {longitude:.4f}"

            # Call Open-Meteo Archive API
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,snowfall_sum,precipitation_hours,wind_speed_10m_max,wind_gusts_10m_max,uv_index_max",
                "timezone": "auto",
            }

            response = requests.get(
                "https://archive-api.open-meteo.com/v1/archive",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Format the response as a readable string
            daily = data.get("daily", {})

            # Build formatted output
            output = f"""Historical Weather Data for {latitude:.4f}, {longitude:.4f}
Location: {location_name}
Period: {start_date} to {end_date}

Daily Historical Summary:"""

            # Add daily historical data
            if daily and "time" in daily:
                for i in range(len(daily.get("time", []))):
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
                    wind_max = (
                        daily.get("wind_speed_10m_max", [])[i]
                        if i < len(daily.get("wind_speed_10m_max", []))
                        else "N/A"
                    )
                    uv_max = (
                        daily.get("uv_index_max", [])[i]
                        if i < len(daily.get("uv_index_max", []))
                        else "N/A"
                    )

                    output += f"\n\n{date}:"
                    output += f"\n- Temperature: High {temp_max}°C, Low {temp_min}°C"
                    output += f"\n- Precipitation: {precip}mm"
                    output += f"\n- Max Wind Speed: {wind_max} km/h"
                    output += f"\n- Max UV Index: {uv_max}"

            # Add summary statistics
            if daily:
                temp_maxes = [
                    t for t in daily.get("temperature_2m_max", []) if t is not None
                ]
                temp_mins = [
                    t for t in daily.get("temperature_2m_min", []) if t is not None
                ]
                precips = [
                    p for p in daily.get("precipitation_sum", []) if p is not None
                ]

                if temp_maxes and temp_mins and precips:
                    output += f"\n\nPeriod Summary:"
                    output += (
                        f"\n- Average High: {sum(temp_maxes)/len(temp_maxes):.1f}°C"
                    )
                    output += f"\n- Average Low: {sum(temp_mins)/len(temp_mins):.1f}°C"
                    output += f"\n- Total Precipitation: {sum(precips):.1f}mm"

            return output

        except Exception as e:
            return f"Error retrieving historical weather: {str(e)}"

    def execute(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> str:
        if self.mock_results:
            return self._mock_results(latitude, longitude, start_date, end_date)
        else:
            return self._real_call(latitude, longitude, start_date, end_date)

    def get_test_cases(self) -> list[dict]:
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

        return [
            {
                "description": "Get historical weather for a week by location",
                "inputs": {
                    "location": "San Francisco, CA",
                    "start_date": month_ago,
                    "end_date": week_ago,
                },
            },
            {
                "description": "Get historical weather by coordinates",
                "inputs": {
                    "latitude": 48.8566,
                    "longitude": 2.3522,
                    "start_date": two_weeks_ago,
                    "end_date": week_ago,
                },
            },
            {
                "description": "Get single day historical weather",
                "inputs": {
                    "location": "Tokyo, Japan",
                    "start_date": week_ago,
                    "end_date": week_ago,
                },
            },
        ]
