"""Weather historical activity that calls the MCP server via HTTP."""
from datetime import datetime, timedelta
from typing import Any, Dict

from temporalio import activity

from .mcp_utils import call_mcp_tool, create_error_response, get_user_display_name


@activity.defn
async def weather_historical_activity(
    user_message: str, user_name: str = "anonymous"
) -> Dict[str, Any]:
    """
    Activity that calls the weather historical MCP server via HTTP.

    Args:
        user_message: The user's message (not used in current implementation)
        user_name: The name of the user making the request

    Returns:
        Dictionary with friendly historical weather message
    """
    # Extract display name for personalization
    display_name = get_user_display_name(user_name)

    try:
        # Call the historical weather tool with Brisbane location and yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        result = await call_mcp_tool(
            service_name="historical",
            tool_name="historical_get_historical_weather",
            tool_args={"location": "Brisbane", "date": yesterday},
            user_name=user_name,
        )

        # Since historical server returns simple string responses, handle accordingly
        if "error" in result:
            return create_error_response(user_name, result["error"])

        # For the mock historical server, the result might be a simple message
        historical_data = result.get("result", str(result))

        # Format friendly response message
        message = f"Hey {display_name}! Here's historical weather information:\n\n"
        message += f"📅 Historical Data: {historical_data}\n"

        # Try to get climate average for current month as well
        current_month = datetime.now().month
        try:
            climate_result = await call_mcp_tool(
                service_name="historical",
                tool_name="historical_get_climate_average",
                tool_args={"location": "Brisbane", "month": current_month},
                user_name=user_name,
            )

            climate_data = climate_result.get("result", str(climate_result))
            message += f"📊 Climate Average: {climate_data}\n"

        except Exception as e:
            activity.logger.warning(f"Could not get climate average: {e}")

        # Add a friendly closing
        message += f"\nHistorical context can be really helpful! 📚"

        return {
            "message": message,
            "location": "Brisbane",
            "historical_data": historical_data,
        }

    except Exception as e:
        activity.logger.error(f"Error getting historical weather: {e}")
        return create_error_response(user_name, f"getting historical weather: {str(e)}")
