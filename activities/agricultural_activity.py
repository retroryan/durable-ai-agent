"""Agricultural activity that calls the MCP server via HTTP."""
from typing import Any, Dict

from temporalio import activity

from .mcp_utils import call_mcp_tool, create_error_response, get_user_display_name


@activity.defn
async def agricultural_activity(
    user_message: str, user_name: str = "anonymous"
) -> Dict[str, Any]:
    """
    Activity that calls the agricultural MCP server via HTTP.

    Args:
        user_message: The user's message (not used in current implementation)
        user_name: The name of the user making the request

    Returns:
        Dictionary with friendly agricultural conditions message
    """
    # Extract display name for personalization
    display_name = get_user_display_name(user_name)

    try:
        # Call the agricultural conditions tool with default farm location
        result = await call_mcp_tool(
            service_name="agricultural",
            tool_name="get_agricultural_conditions",
            tool_args={
                "request": {"location": "Central Valley, California", "days": 5}
            },
            user_name=user_name,
        )

        # Handle error responses
        if "error" in result:
            return create_error_response(user_name, result["error"])

        # Extract agricultural information
        location_info = result.get("location_info", {})
        location_name = location_info.get("name", "Unknown location")

        # Get current conditions
        current_data = result.get("current", {})
        current_temp = current_data.get("temperature_2m", "Unknown")
        current_humidity = current_data.get("relative_humidity_2m", "Unknown")

        # Get daily data for soil and evapotranspiration info
        daily_data = result.get("daily", {})
        today_max = daily_data.get("temperature_2m_max", [None])[0]
        today_min = daily_data.get("temperature_2m_min", [None])[0]
        today_precipitation = daily_data.get("precipitation_sum", [None])[0]
        today_et = daily_data.get("et0_fao_evapotranspiration", [None])[0]

        # Get hourly soil moisture data (first few hours)
        hourly_data = result.get("hourly", {})
        soil_moisture_0_1cm = hourly_data.get("soil_moisture_0_to_1cm", [None])[0]
        soil_moisture_1_3cm = hourly_data.get("soil_moisture_1_to_3cm", [None])[0]
        soil_temp_0cm = hourly_data.get("soil_temperature_0cm", [None])[0]

        # Format friendly response message
        message = f"Hey {display_name}! Here are the agricultural conditions for {location_name}:\n\n"

        # Current conditions
        message += f"🌡️ Current temperature: {current_temp}°C\n"
        message += f"💧 Current humidity: {current_humidity}%\n"

        # Daily forecast
        if today_max and today_min:
            message += f"📊 Today's range: {today_min}°C to {today_max}°C\n"

        if today_precipitation:
            message += f"🌧️ Expected precipitation: {today_precipitation}mm\n"

        if today_et:
            message += f"🌱 Evapotranspiration: {today_et:.1f}mm\n"

        # Soil conditions
        message += f"\n🌾 Soil Conditions:\n"
        if soil_temp_0cm:
            message += f"  • Surface temperature: {soil_temp_0cm}°C\n"
        if soil_moisture_0_1cm:
            message += (
                f"  • Top soil moisture (0-1cm): {soil_moisture_0_1cm:.3f} m³/m³\n"
            )
        if soil_moisture_1_3cm:
            message += (
                f"  • Shallow soil moisture (1-3cm): {soil_moisture_1_3cm:.3f} m³/m³\n"
            )

        # Add a friendly closing
        message += f"\nGreat growing conditions ahead! 🚜🌾"

        return {
            "message": message,
            "location": location_name,
            "current_temp": current_temp,
            "soil_moisture": soil_moisture_0_1cm,
            "evapotranspiration": today_et,
        }

    except Exception as e:
        activity.logger.error(f"Error getting agricultural conditions: {e}")
        return create_error_response(
            user_name, f"getting agricultural conditions: {str(e)}"
        )
