import os
from datetime import datetime, timedelta
from typing import ClassVar, Optional, Type

import requests
from pydantic import BaseModel, Field, field_validator

from models.types import MCPConfig
from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool
from tools.mcp_utils import execute_mcp_sync


class HistoricalRequest(BaseModel):
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
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")

    @field_validator("latitude", "longitude", mode="before")
    def convert_to_float(cls, v):
        if v is not None and isinstance(v, str):
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


class HistoricalWeatherTool(MCPTool):
    NAME: ClassVar[str] = "get_historical_weather"
    MODULE: ClassVar[str] = "tools.agriculture.historical_weather"
    is_mcp: ClassVar[bool] = True

    description: str = (
        "Get historical weather data for a location. Retrieves past temperature, "
        "precipitation, and weather conditions for any date range at least 5 days ago."
    )
    args_model: Type[BaseModel] = HistoricalRequest

    # MCP configuration
    # mcp_server_name identifies which MCP server this tool connects to
    # This is used to construct the prefixed tool name when using the proxy
    mcp_server_name: str = "historical"
    
    # Note: get_mcp_config() is inherited from MCPTool base class
    # It handles dynamic tool name resolution based on MCP_USE_PROXY

    def execute(
        self,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        start_date: str = None,
        end_date: str = None,
    ) -> str:
        # Always use MCP execution (MCP server handles mock mode via TOOLS_MOCK env var)
        return execute_mcp_sync(
            self,
            location=location,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date
        )

    def get_test_cases(self) -> list[dict]:
        return [
            {
                "description": "Get historical weather for last week",
                "inputs": {
                    "location": "Chicago, IL",
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-07",
                },
            },
            {
                "description": "Get historical weather by coordinates",
                "inputs": {
                    "latitude": 41.8781,
                    "longitude": -87.6298,
                    "start_date": "2024-12-25",
                    "end_date": "2024-12-31",
                },
            },
            {
                "description": "Get single day historical weather",
                "inputs": {
                    "location": "Denver, CO",
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-01",
                },
            },
        ]