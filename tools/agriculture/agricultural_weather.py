import os
from datetime import datetime, timedelta
from typing import ClassVar, Optional, Type

import requests
from pydantic import BaseModel, Field, field_validator

from models.types import MCPConfig
from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool
from tools.mcp_utils import execute_mcp_sync


class AgriculturalRequest(BaseModel):
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
        default=7, ge=1, le=7, description="Number of forecast days (1-7)"
    )
    crop_type: Optional[str] = Field(
        default=None, description="Type of crop for specialized agricultural conditions"
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


class AgriculturalWeatherTool(MCPTool):
    NAME: ClassVar[str] = "get_agricultural_conditions"
    MODULE: ClassVar[str] = "tools.agriculture.agricultural_weather"
    is_mcp: ClassVar[bool] = True

    description: str = (
        "Get agricultural weather conditions including soil moisture, evapotranspiration, "
        "and growing conditions for a location"
    )
    args_model: Type[BaseModel] = AgriculturalRequest

    # MCP configuration
    # mcp_server_name identifies which MCP server this tool connects to
    # This is used to construct the prefixed tool name when using the proxy
    mcp_server_name: str = "agricultural"
    
    # Note: get_mcp_config() is inherited from MCPTool base class
    # It handles dynamic tool name resolution based on MCP_USE_PROXY

    def execute(
        self,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        days: int = 7,
        crop_type: Optional[str] = None,
    ) -> str:
        # Always use MCP execution (MCP server handles mock mode via TOOLS_MOCK env var)
        return execute_mcp_sync(
            self,
            location=location,
            latitude=latitude,
            longitude=longitude,
            days=days,
            crop_type=crop_type
        )

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