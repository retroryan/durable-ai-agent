"""Common utilities for MCP activities."""
import json
import os
from typing import Any, Dict, Optional

from temporalio import activity

from shared.mcp_client_manager_v2 import MCPClientManager


def get_user_display_name(user_name: str) -> str:
    """Extract display name from user_name for personalization."""
    return (
        user_name.split("_")[0] + "_" + user_name.split("_")[1]
        if "_" in user_name
        else user_name
    )


def get_mcp_server_config(service_name: str) -> Dict[str, str]:
    """Get MCP server configuration from environment variables.

    Args:
        service_name: Service name (forecast, historical, agricultural)

    Returns:
        Dictionary with server configuration
    """
    service_configs = {
        "forecast": {
            "host_var": "MCP_FORECAST_SERVER_HOST",
            "port_var": "MCP_FORECAST_SERVER_PORT",
            "url_var": "MCP_FORECAST_SERVER_URL",
            "default_host": "forecast-mcp",
            "default_port": "7778",
        },
        "historical": {
            "host_var": "MCP_HISTORICAL_SERVER_HOST",
            "port_var": "MCP_HISTORICAL_SERVER_PORT",
            "url_var": "MCP_HISTORICAL_SERVER_URL",
            "default_host": "historical-mcp",
            "default_port": "7779",
        },
        "agricultural": {
            "host_var": "MCP_AGRICULTURAL_SERVER_HOST",
            "port_var": "MCP_AGRICULTURAL_SERVER_PORT",
            "url_var": "MCP_AGRICULTURAL_SERVER_URL",
            "default_host": "agricultural-mcp",
            "default_port": "7780",
        },
    }

    if service_name not in service_configs:
        raise ValueError(f"Unknown service: {service_name}")

    config = service_configs[service_name]
    host = os.getenv(config["host_var"], config["default_host"])
    port = os.getenv(config["port_var"], config["default_port"])
    url = os.getenv(config["url_var"], f"http://{host}:{port}/mcp")

    return {"host": host, "port": port, "url": url}


def create_http_server_def(service_name: str, mcp_url: str) -> Dict[str, Any]:
    """Create HTTP server definition for MCP client."""
    return {
        "name": f"{service_name}-server-http",
        "connection_type": "http",
        "url": mcp_url,
        "env": None,
    }


def parse_mcp_result(result: Any) -> Dict[str, Any]:
    """Parse MCP result and extract JSON data.

    Args:
        result: Result from MCP client call_tool

    Returns:
        Parsed JSON data
    """
    if isinstance(result, list):
        # For list results, get the first text content
        text_content = result[0].text if hasattr(result[0], "text") else str(result[0])
        return json.loads(text_content)
    else:
        # For single result, get the first content item's text
        content_item = result.content[0]
        text_content = (
            content_item.text if hasattr(content_item, "text") else str(content_item)
        )
        return json.loads(text_content)


async def call_mcp_tool(
    service_name: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    user_name: str = "anonymous",
) -> Dict[str, Any]:
    """Generic function to call an MCP tool.

    Args:
        service_name: Name of the MCP service (forecast, historical, agricultural)
        tool_name: Name of the tool to call
        tool_args: Arguments to pass to the tool
        user_name: User making the request

    Returns:
        Parsed result from the tool call
    """
    # Get server configuration
    config = get_mcp_server_config(service_name)
    mcp_url = config["url"]

    # Get activity info for context
    info = activity.info()
    workflow_id = info.workflow_id

    # Log the activity execution with user context
    activity.logger.info(
        f"User '{user_name}' (workflow: {workflow_id}) calling {tool_name} on {service_name} at {mcp_url}"
    )

    # Create MCP client manager
    manager = MCPClientManager()

    # HTTP server definition
    http_server_def = create_http_server_def(service_name, mcp_url)

    try:
        # Get client connection
        client = await manager.get_client(http_server_def)
        activity.logger.info(f"Successfully connected to {service_name} MCP server")

        # Call the tool
        result = await client.call_tool(tool_name, tool_args)

        # Parse and return result
        data = parse_mcp_result(result)

        # Cleanup the manager
        await manager.cleanup()

        return data

    except Exception as e:
        activity.logger.error(f"Error calling {tool_name} on {service_name}: {e}")

        # Cleanup on error
        try:
            await manager.cleanup()
        except Exception:
            pass  # Ignore cleanup errors

        raise e


def create_error_response(user_name: str, error_message: str) -> Dict[str, Any]:
    """Create a standardized error response.

    Args:
        user_name: User name for personalization
        error_message: Error message to include

    Returns:
        Standardized error response
    """
    display_name = get_user_display_name(user_name)
    return {
        "message": f"Sorry {display_name}, I encountered an error: {str(error_message)}",
        "error": True,
        "details": str(error_message),
    }
