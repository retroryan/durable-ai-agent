"""Weather forecast activity that calls the MCP server via HTTP."""
import json
import os
from typing import Any, Dict

from temporalio import activity

from shared.mcp_client_manager import MCPClientManager


@activity.defn
async def weather_forecast_activity(
    user_message: str, user_name: str = "anonymous"
) -> Dict[str, Any]:
    """
    Activity that calls the weather forecast MCP server via HTTP.

    Args:
        user_message: The user's message (not used in current implementation)
        user_name: The name of the user making the request

    Returns:
        Dictionary with friendly weather forecast message
    """
    # Get MCP server configuration from environment
    mcp_host = os.getenv("MCP_FORECAST_SERVER_HOST", "forecast-mcp")
    mcp_port = os.getenv("MCP_FORECAST_SERVER_PORT", "7778")
    mcp_url = os.getenv("MCP_FORECAST_SERVER_URL", f"http://{mcp_host}:{mcp_port}/mcp")

    # Get activity info for context
    info = activity.info()
    workflow_id = info.workflow_id

    # Extract display name for personalization
    display_name = (
        user_name.split("_")[0] + "_" + user_name.split("_")[1]
        if "_" in user_name
        else user_name
    )

    # Log the activity execution with user context
    activity.logger.info(
        f"User '{user_name}' (workflow: {workflow_id}) requesting weather forecast from {mcp_url}"
    )

    # Create MCP client manager
    manager = MCPClientManager()

    # HTTP server definition
    http_server_def = {
        "name": "forecast-server-http",
        "connection_type": "http",
        "url": mcp_url,
        "env": None,
    }

    try:
        # Get client connection
        client = await manager.get_client(http_server_def)
        activity.logger.info("Successfully connected to weather forecast MCP server")

        # Call the weather forecast tool with New York location and 3 days
        result = await client.call_tool(
            "get_weather_forecast", {"request": {"location": "New York", "days": 3}}
        )

        # Handle result format (list of TextContent objects)
        if isinstance(result, list):
            # For list results, get the first text content
            text_content = (
                result[0].text if hasattr(result[0], "text") else str(result[0])
            )
            data = json.loads(text_content)
        else:
            # For single result, get the first content item's text
            content_item = result.content[0]
            text_content = (
                content_item.text
                if hasattr(content_item, "text")
                else str(content_item)
            )
            data = json.loads(text_content)

        # Extract weather information
        location_name = data.get("location_info", {}).get("name", "Unknown location")
        current_temp = data.get("current", {}).get("temperature_2m", "Unknown")

        # Get today's forecast from daily data
        daily_data = data.get("daily", {})
        today_max = daily_data.get("temperature_2m_max", [None])[0]
        today_min = daily_data.get("temperature_2m_min", [None])[0]

        # Format friendly response message
        message = (
            f"Hey {display_name}! Here's your weather forecast for {location_name}:\n\n"
        )
        message += f"🌡️ Current temperature: {current_temp}°C\n"

        if today_max and today_min:
            message += f"📊 Today's range: {today_min}°C to {today_max}°C\n"

        # Add a friendly closing
        message += f"\nStay comfortable out there! 🌤️"

        # Cleanup the manager
        await manager.cleanup()

        return {
            "message": message,
            "location": location_name,
            "current_temp": current_temp,
        }

    except Exception as e:
        activity.logger.error(f"Error getting weather forecast: {e}")

        # Cleanup on error
        try:
            await manager.cleanup()
        except Exception:
            pass  # Ignore cleanup errors

        return {
            "message": f"Sorry {display_name}, I encountered an error while getting the weather forecast: {str(e)}",
            "location": "Unknown",
            "current_temp": "Unknown",
        }
