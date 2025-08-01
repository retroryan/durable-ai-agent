"""Weather activities that delegate to existing weather utilities.

These activities serve as a thin wrapper around the existing weather
utilities, preserving all existing functionality while enabling
Temporal's durability features.
"""
from typing import Dict
from temporalio import activity

from models.mcp_models import ForecastRequest, HistoricalRequest, AgriculturalRequest
from mcp_servers.utils.weather_utils import (
    get_forecast_data,
    get_historical_data,
    get_agricultural_data,
)


@activity.defn
async def get_weather_forecast_activity(params: Dict) -> Dict:
    """Get weather forecast using existing utilities.
    
    Args:
        params: Dictionary containing ForecastRequest fields
        
    Returns:
        Weather forecast data in exact existing format
    """
    
    # Reconstruct Pydantic model for validation
    request = ForecastRequest(**params)
    
    # Delegate to existing utility
    result = await get_forecast_data(request)
    
    return result


@activity.defn
async def get_historical_weather_activity(params: Dict) -> Dict:
    """Get historical weather using existing utilities.
    
    Args:
        params: Dictionary containing HistoricalRequest fields
        
    Returns:
        Historical weather data in exact existing format
    """
    # Reconstruct Pydantic model for validation
    request = HistoricalRequest(**params)
    
    # Delegate to existing utility
    result = await get_historical_data(request)
    
    return result


@activity.defn
async def get_agricultural_conditions_activity(params: Dict) -> Dict:
    """Get agricultural conditions using existing utilities.
    
    Args:
        params: Dictionary containing AgriculturalRequest fields
        
    Returns:
        Agricultural conditions data in exact existing format
    """
    # Reconstruct Pydantic model for validation
    request = AgriculturalRequest(**params)
    
    # Delegate to existing utility
    result = await get_agricultural_data(request)
    
    return result