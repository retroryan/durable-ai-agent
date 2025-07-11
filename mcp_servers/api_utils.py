"""
Unified OpenMeteo API client for weather and agricultural data.

This client provides a comprehensive interface to Open-Meteo's free weather API,
demonstrating clean async patterns for a modern Python application.
No authentication required - just make requests and get data!
"""

import httpx
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta, date


# API Type Constants
API_TYPE_FORECAST = "forecast"
API_TYPE_ARCHIVE = "archive"
API_TYPE_GEOCODING = "geocoding"


# Helper function for servers
async def get_coordinates(location: str) -> Optional[Dict[str, Union[str, float]]]:
    """
    Get coordinates for a location name.
    Returns dict with latitude, longitude, and name, or None if not found.
    """
    client = OpenMeteoClient()
    try:
        lat, lon = await client.get_coordinates(location)
        return {
            "latitude": lat,
            "longitude": lon,
            "name": location
        }
    except Exception:
        return None



# Parameter helpers
def get_daily_params() -> List[str]:
    """Get standard daily parameters for forecast."""
    return [
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "rain_sum",
        "snowfall_sum",
        "precipitation_hours",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "uv_index_max"
    ]


def get_hourly_params() -> List[str]:
    """Get standard hourly parameters for forecast."""
    return [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "showers",
        "snowfall",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m"
    ]


class OpenMeteoClient:
    """
    Async-only client for Open-Meteo API demonstrating good patterns:
    - Clean async/await usage
    - Proper resource management with context managers
    - Connection pooling through client reuse
    """
    
    def __init__(self):
        """Initialize the Open-Meteo client."""
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.archive_url = "https://archive-api.open-meteo.com/v1/archive"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self._client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
            
    async def ensure_client(self) -> httpx.AsyncClient:
        """Ensure we have an active client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
        
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get(self, api_type: str, params: Dict) -> Dict:
        """Generic method to get data from Open-Meteo APIs."""
        client = await self.ensure_client()
        
        if api_type == API_TYPE_FORECAST:
            url = self.forecast_url
        elif api_type == API_TYPE_ARCHIVE:
            url = self.archive_url
        elif api_type == API_TYPE_GEOCODING:
            url = self.geocoding_url
        else:
            raise ValueError(f"Unknown API type: {api_type}")
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_coordinates(self, location: str) -> Tuple[float, float]:
        """
        Convert location name to coordinates.
        
        Args:
            location: Location name (e.g., "New York", "London, UK")
            
        Returns:
            Tuple of (latitude, longitude)
            
        Raises:
            ValueError: If location not found
        """
        # Extract just the city name from formats like "City, State"
        city = location.split(',')[0].strip()
        
        results = await self.geocode(city, count=1)
        if results:
            loc = results[0]
            return loc["latitude"], loc["longitude"]
            
        raise ValueError(f"Location '{location}' not found")
    
    async def geocode(self, name: str, count: int = 10) -> List[Dict]:
        """
        Search for locations by name and get their coordinates.
        
        Args:
            name: Name of the location to search for
            count: Maximum number of results to return (default: 10)
        
        Returns:
            List of matching locations with coordinates
        """
        client = await self.ensure_client()
        
        params = {
            "name": name,
            "count": count,
            "language": "en",
            "format": "json"
        }
        
        response = await client.get(self.geocoding_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    
    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        hourly: Optional[List[str]] = None,
        daily: Optional[List[str]] = None,
        current: Optional[List[str]] = None,
        forecast_days: int = 7,
        past_days: int = 0,
        timezone: str = "auto"
    ) -> Dict:
        """
        Get weather forecast data for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            hourly: List of hourly variables to fetch
            daily: List of daily variables to fetch
            current: List of current weather variables
            forecast_days: Number of forecast days (max 16)
            past_days: Number of past days to include
            timezone: Timezone (default "auto")
        
        Returns:
            Dictionary with requested weather data
        """
        client = await self.ensure_client()
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": forecast_days,
            "past_days": past_days,
            "timezone": timezone
        }
        
        # Add optional parameters
        if hourly:
            params["hourly"] = ",".join(hourly)
        if daily:
            params["daily"] = ",".join(daily)
        if current:
            params["current"] = ",".join(current)
        
        response = await client.get(self.forecast_url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_historical(
        self,
        latitude: float,
        longitude: float,
        start_date: Union[str, date],
        end_date: Union[str, date],
        hourly: Optional[List[str]] = None,
        daily: Optional[List[str]] = None,
        timezone: str = "auto"
    ) -> Dict:
        """
        Get historical weather data for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date (YYYY-MM-DD or date object)
            end_date: End date (YYYY-MM-DD or date object)
            hourly: List of hourly variables to fetch
            daily: List of daily variables to fetch
            timezone: Timezone (default "auto")
        
        Returns:
            Dictionary with historical weather data
        """
        client = await self.ensure_client()
        
        # Convert dates to strings if needed
        if isinstance(start_date, date):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, date):
            end_date = end_date.strftime("%Y-%m-%d")
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone
        }
        
        # Add optional parameters
        if hourly:
            params["hourly"] = ",".join(hourly)
        if daily:
            params["daily"] = ",".join(daily)
        
        response = await client.get(self.archive_url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_weather_data(
        self,
        latitude: float,
        longitude: float,
        parameters: List[str],
        start_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        timezone: str = "auto"
    ) -> Dict:
        """
        Unified method to get weather data (forecast or historical).
        
        Automatically determines whether to use forecast or archive API
        based on the requested date range.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            parameters: List of weather parameters to fetch
            start_date: Start date (optional, defaults to today)
            end_date: End date (optional, defaults to 7 days from start)
            timezone: Timezone (default "auto")
        
        Returns:
            Dictionary with weather data
        """
        # Determine date range
        today = datetime.now().date()
        
        if start_date is None:
            start_date = today
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()
        
        if end_date is None:
            end_date = start_date + timedelta(days=7)
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()
        
        # Determine which API to use
        archive_cutoff = today - timedelta(days=5)
        
        if end_date <= archive_cutoff:
            # All dates are historical
            return await self.get_historical(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                daily=parameters,
                timezone=timezone
            )
        elif start_date >= today:
            # All dates are forecast
            forecast_days = (end_date - today).days + 1
            return await self.get_forecast(
                latitude=latitude,
                longitude=longitude,
                daily=parameters,
                forecast_days=min(forecast_days, 16),
                timezone=timezone
            )
        else:
            # Mixed: need both historical and forecast
            # For simplicity in this demo, just get forecast data
            forecast_days = (end_date - today).days + 1
            past_days = (today - start_date).days
            return await self.get_forecast(
                latitude=latitude,
                longitude=longitude,
                daily=parameters,
                forecast_days=min(forecast_days, 16),
                past_days=min(past_days, 92),
                timezone=timezone
            )

