"""Weather workflows that orchestrate weather data retrieval.

These workflows provide durability and retry logic for weather operations
while delegating all business logic to existing utilities via activities.
"""
# Import only the bare minimum before enabling unsafe imports
from temporalio import workflow

# Enable unsafe imports for the rest of the module
with workflow.unsafe.imports_passed_through():
    from datetime import timedelta
    from typing import Dict
    from temporalio.common import RetryPolicy


@workflow.defn
class GetWeatherForecastWorkflow:
    """Workflow for retrieving weather forecast data with durability."""
    
    @workflow.run
    async def run(self, params: Dict) -> Dict:
        """Execute the weather forecast workflow.
        
        Args:
            params: Dictionary containing ForecastRequest fields
            
        Returns:
            Weather forecast data maintaining exact API response format
        """
        # Use string reference to activity to avoid import restrictions
        return await workflow.execute_activity(
            "get_weather_forecast_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2,
            ),
        )


@workflow.defn  
class GetHistoricalWeatherWorkflow:
    """Workflow for retrieving historical weather data with durability."""
    
    @workflow.run
    async def run(self, params: Dict) -> Dict:
        """Execute the historical weather workflow.
        
        Args:
            params: Dictionary containing HistoricalRequest fields
            
        Returns:
            Historical weather data maintaining exact API response format
        """
        # Use string reference to activity to avoid import restrictions
        return await workflow.execute_activity(
            "get_historical_weather_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2,
            ),
        )


@workflow.defn
class GetAgriculturalConditionsWorkflow:
    """Workflow for retrieving agricultural weather conditions with durability."""
    
    @workflow.run
    async def run(self, params: Dict) -> Dict:
        """Execute the agricultural conditions workflow.
        
        Args:
            params: Dictionary containing AgriculturalRequest fields
            
        Returns:
            Agricultural conditions data maintaining exact API response format
        """
        # Use string reference to activity to avoid import restrictions
        return await workflow.execute_activity(
            "get_agricultural_conditions_activity",
            params,
            schedule_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                backoff_coefficient=2,
            ),
        )