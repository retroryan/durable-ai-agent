#!/usr/bin/env python3
"""
Unified MCP server for all weather and agricultural data.
Now with Temporal workflow integration for durability.
"""

import argparse
import os
import logging
import time
import uuid

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from models.mcp_models import ForecastRequest, HistoricalRequest, AgriculturalRequest
from mcp_servers.utils.weather_utils import MOCK_MODE

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporal imports
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from dotenv import load_dotenv

# Import workflow classes for execute_workflow
from mcp_servers.weather_workflows_safe import (
    GetWeatherForecastWorkflow,
    GetHistoricalWeatherWorkflow,
    GetAgriculturalConditionsWorkflow
)

# Load environment variables
load_dotenv(override=True)

# Temporal connection settings
TEMPORAL_ADDRESS = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")

async def get_temporal_client() -> Client:
    """
    Creates a Temporal client based on environment configuration.
    Simplified version for MCP server use.
    """
    logger.info(f"Connecting to Temporal at {TEMPORAL_ADDRESS}")
    return await Client.connect(
        TEMPORAL_ADDRESS,
        namespace=TEMPORAL_NAMESPACE,
        data_converter=pydantic_data_converter,
    )

if MOCK_MODE:
    logger.info("🔧 Running weather server in MOCK MODE - no external API calls will be made")

# One server to rule them all
server = FastMCP(name="weather-mcp")


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy", 
        "service": "weather-server",
        "tools": ["get_weather_forecast", "get_historical_weather", "get_agricultural_conditions"],
        "mock_mode": MOCK_MODE,
        "mode": "temporal-workflows"
    })


@server.tool
async def get_weather_forecast(request: ForecastRequest) -> dict:
    """Get weather forecast for a location.
    
    Performance tip: Providing latitude/longitude is 3x faster than location name.
    Pydantic automatically handles type conversion from strings to floats.
    
    Args:
        request: ForecastRequest with location/coordinates and days
        
    Returns:
        Structured forecast data with location info, current conditions, and daily/hourly data
    """
    client = await get_temporal_client()
    
    # Create unique workflow ID
    workflow_id = f"forecast-{uuid.uuid4().hex[:8]}-{int(time.time())}"
    
    
    try:
        # Execute workflow and wait for result
        result = await client.execute_workflow(
            GetWeatherForecastWorkflow.run,
            request.model_dump(),
            id=workflow_id,
            task_queue="durable-ai-agent-tasks"
        )
        return result
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {str(e)}")
        raise


@server.tool
async def get_historical_weather(request: HistoricalRequest) -> dict:
    """Get historical weather data for a location.
    
    Performance tip: Providing latitude/longitude is 3x faster than location name.
    Pydantic automatically handles type conversion and date validation.
    
    Args:
        request: HistoricalRequest with dates and location/coordinates
        
    Returns:
        Structured historical weather data with daily aggregates
    """
    client = await get_temporal_client()
    
    # Create unique workflow ID
    workflow_id = f"historical-{uuid.uuid4().hex[:8]}-{int(time.time())}"
    
    
    try:
        # Execute workflow and wait for result
        result = await client.execute_workflow(
            GetHistoricalWeatherWorkflow.run,
            request.model_dump(),
            id=workflow_id,
            task_queue="durable-ai-agent-tasks"
        )
        return result
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {str(e)}")
        raise


@server.tool
async def get_agricultural_conditions(request: AgriculturalRequest) -> dict:
    """Get agricultural weather conditions for a location.
    
    Performance tip: Providing latitude/longitude is 3x faster than location name.
    Pydantic automatically handles type conversion from strings to floats.
    
    Args:
        request: AgriculturalRequest with location/coordinates and days
        
    Returns:
        Structured agricultural data with soil moisture, evapotranspiration, and growing conditions
    """
    client = await get_temporal_client()
    
    # Create unique workflow ID
    workflow_id = f"agricultural-{uuid.uuid4().hex[:8]}-{int(time.time())}"
    
    
    try:
        # Execute workflow and wait for result
        result = await client.execute_workflow(
            GetAgriculturalConditionsWorkflow.run,
            request.model_dump(),
            id=workflow_id,
            task_queue="durable-ai-agent-tasks"
        )
        return result
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Unified MCP Weather Server")
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "http", "sse", "streamable-http"],
        default="streamable-http",
        help="Transport protocol to use (default: streamable-http)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv(
            "MCP_HOST", "0.0.0.0" if os.path.exists("/.dockerenv") else "127.0.0.1"
        ),
        help="Host to bind to (for HTTP transports)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "7778")),
        help="Port to bind to (for HTTP transports)",
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="URL path for HTTP transports (default: /mcp)",
    )
    args = parser.parse_args()

    # Run the server with appropriate transport
    if args.transport == "stdio":
        # For stdio, we don't need host/port
        server.run(transport="stdio")
    else:
        # For HTTP transports, include host/port/path
        print(f"Starting unified weather server on {args.host}:{args.port}{args.path}")
        print(f"Mock mode: {'ON' if MOCK_MODE else 'OFF'}")
        print("Available tools:")
        print("  - get_weather_forecast")
        print("  - get_historical_weather")
        print("  - get_agricultural_conditions")
        server.run(
            transport=args.transport,
            host=args.host,
            port=args.port,
            path=args.path,
        )