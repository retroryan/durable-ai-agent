import asyncio
import os
from typing import Any, Dict

from fastmcp import Client
from temporalio import activity

from models.tool_definitions import MCPServerDefinition


class MCPClientManager:
    """Manages pooled MCP client connections for reuse across tool calls"""

    def __init__(self):
        self._clients: Dict[str, Client] = {}
        self._lock = asyncio.Lock()

    async def get_client(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> Client:
        """Return existing client or create new one, keyed by server definition hash"""
        async with self._lock:
            key = self._get_server_key(server_def)
            if key not in self._clients:
                await self._create_client(server_def, key)
                activity.logger.info(
                    f"Created new MCP client for {self._get_server_name(server_def)}"
                )
            else:
                activity.logger.info(
                    f"Reusing existing MCP client for {self._get_server_name(server_def)}"
                )
            return self._clients[key]

    def _get_server_key(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> str:
        """Generate unique key for server definition"""
        if server_def is None:
            return "default:python:server.py"

        # Handle both MCPServerDefinition objects and dicts (from Temporal serialization)
        if isinstance(server_def, dict):
            name = server_def.get("name", "default")
            command = server_def.get("command", "python")
            args = server_def.get("args", ["server.py"])
        else:
            name = server_def.name
            command = server_def.command
            args = server_def.args

        return f"{name}:{command}:{':'.join(args)}"

    def _get_server_name(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> str:
        """Get server name for logging"""
        if server_def is None:
            return "default"

        if isinstance(server_def, dict):
            return server_def.get("name", "default")
        else:
            return server_def.name

    def _build_transport(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> str | Dict[str, Any]:
        """Build transport specification from MCPServerDefinition or dict"""
        if server_def is None:
            # Default to stdio connection with server.py
            return "server.py"

        # Handle both MCPServerDefinition objects and dicts (from Temporal serialization)
        if isinstance(server_def, dict):
            conn_type = server_def.get("connection_type", "stdio")
            if conn_type == "http":
                # For HTTP, return the URL directly
                return server_def.get("url", "http://localhost:8000/mcp")
            else:
                # For stdio, we need to check if it's a simple script path
                # or a more complex command with args
                command = server_def.get("command", "python")
                args = server_def.get("args", ["server.py"])
                env = server_def.get("env", {})

                # If it's just python script.py, return the script path
                if command == "python" and len(args) == 1 and args[0].endswith(".py"):
                    return args[0]
                else:
                    # Otherwise, use MCPConfig format for stdio
                    return {
                        "mcpServers": {
                            "server": {
                                "transport": "stdio",
                                "command": command,
                                "args": args,
                                "env": env or {},
                            }
                        }
                    }
        else:
            # Handle MCPServerDefinition object
            if server_def.connection_type == "http":
                return server_def.url or "http://localhost:8000/mcp"
            else:
                # For stdio
                if (
                    server_def.command == "python"
                    and len(server_def.args) == 1
                    and server_def.args[0].endswith(".py")
                ):
                    return server_def.args[0]
                else:
                    return {
                        "mcpServers": {
                            "server": {
                                "transport": "stdio",
                                "command": server_def.command,
                                "args": server_def.args,
                                "env": server_def.env or {},
                            }
                        }
                    }

    async def _create_client(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None, key: str
    ):
        """Create and store new client connection"""
        transport = self._build_transport(server_def)

        # Create FastMCP client
        client = Client(transport)

        # Initialize the client (enter context)
        await client.__aenter__()

        # Store the client
        self._clients[key] = client

    async def cleanup(self):
        """Close all connections gracefully"""
        async with self._lock:
            # Close all client sessions
            for client in self._clients.values():
                try:
                    await client.__aexit__(None, None, None)
                except Exception as e:
                    activity.logger.warning(f"Error closing MCP client: {e}")

            self._clients.clear()
            activity.logger.info("All MCP connections closed")
