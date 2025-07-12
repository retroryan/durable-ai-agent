"""
Simple service manager for MCP weather services.

This is a DEMO implementation - prioritizes clarity over complexity.
"""

import logging
from pathlib import Path
from typing import Any, Dict

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


class WeatherServiceManager:
    """Manages lifecycle of weather service proxies."""

    def __init__(self):
        """Initialize the service manager."""
        self.proxies: Dict[str, FastMCP] = {}
        self._initialized = False

    async def start_all(self):
        """Start all weather service proxies."""
        if self._initialized:
            return

        # For this demo, we'll import and create the services directly
        # In a real implementation, these would be separate processes/servers

        try:
            # Import the real service modules from mcp_servers
            from mcp_servers import (
                agricultural_server,
                forecast_server,
                historical_server,
            )

            # Create proxies for each service
            # Using FastMCP.as_proxy() with the server instances
            self.proxies["forecast"] = FastMCP.as_proxy(
                forecast_server.server, name="forecast_proxy"
            )
            logger.info("Created proxy for forecast service")

            self.proxies["agricultural"] = FastMCP.as_proxy(
                agricultural_server.server, name="agricultural_proxy"
            )
            logger.info("Created proxy for agricultural service")

            self.proxies["historical"] = FastMCP.as_proxy(
                historical_server.server, name="historical_proxy"
            )
            logger.info("Created proxy for historical service")

        except Exception as e:
            logger.error(f"Failed to create proxies: {e}")
            raise

        self._initialized = True
        logger.info(f"Initialized {len(self.proxies)} service proxies")

    def get_proxy(self, service_name: str) -> FastMCP | None:
        """Get a proxy for the specified service."""
        return self.proxies.get(service_name)

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all services."""
        health_status = {}

        for name in ["forecast", "agricultural", "historical"]:
            # Simple check - just verify proxy exists
            # In a real implementation, you might ping the actual service
            health_status[name] = name in self.proxies

        return health_status

    async def shutdown(self):
        """Shutdown all services."""
        # FastMCP proxies handle their own cleanup
        self.proxies.clear()
        self._initialized = False
        logger.info("All services shut down")
