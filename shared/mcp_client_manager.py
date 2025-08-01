import asyncio
import logging
from typing import Any, Dict, Optional, Callable

from fastmcp import Client
from temporalio import activity

from models.tool_definitions import MCPServerDefinition


class MCPClientManager:
    """FastMCP-aligned client manager that follows official documentation patterns.
    
    This implementation strictly follows the FastMCP documentation requirement:
    'All client operations require using the async with context manager for 
    proper connection lifecycle management.'
    
    NO connection pooling, NO stored clients, NO compatibility layers.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    async def execute_tool(
        self,
        server_def: MCPServerDefinition | Dict[str, Any] | None,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: float = 60.0,
        max_retries: int = 3,
        log_handler: Optional[Callable] = None,
        progress_handler: Optional[Callable] = None
    ) -> Any:
        """Execute a tool following FastMCP's context manager pattern.
        
        Args:
            server_def: Server definition for transport configuration
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            timeout: Operation timeout in seconds
            max_retries: Number of retry attempts
            log_handler: Optional handler for server log messages
            progress_handler: Optional handler for progress updates
            
        Returns:
            Tool execution result
            
        Raises:
            Exception: After all retry attempts are exhausted
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                transport = self._build_transport(server_def)
                
                # Create client with optional handlers
                client = Client(
                    transport,
                    timeout=timeout,
                    log_handler=log_handler or self._default_log_handler,
                    progress_handler=progress_handler
                )
                
                # Use client within context manager as required by docs
                async with client:
                    return await client.call_tool(tool_name, arguments)
                    
            except Exception as e:
                last_error = e
                self._logger.warning(
                    f"Tool '{tool_name}' execution attempt {attempt + 1}/{max_retries} "
                    f"failed: {type(e).__name__}: {e}"
                )
                
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s...
                    delay = 2 ** attempt
                    self._logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    
        # All retries exhausted
        self._logger.error(
            f"Tool '{tool_name}' failed after {max_retries} attempts"
        )
        raise last_error

    async def list_tools(
        self,
        server_def: MCPServerDefinition | Dict[str, Any] | None,
        timeout: float = 30.0
    ) -> list:
        """List available tools from server.
        
        Args:
            server_def: Server definition for transport configuration
            timeout: Operation timeout in seconds
            
        Returns:
            List of available tools
        """
        transport = self._build_transport(server_def)
        
        client = Client(transport, timeout=timeout)
        async with client:
            return await client.list_tools()

    async def get_resource(
        self,
        server_def: MCPServerDefinition | Dict[str, Any] | None,
        uri: str,
        timeout: float = 30.0
    ) -> Any:
        """Get a resource from the server.
        
        Args:
            server_def: Server definition for transport configuration
            uri: Resource URI
            timeout: Operation timeout in seconds
            
        Returns:
            Resource content
        """
        transport = self._build_transport(server_def)
        
        client = Client(transport, timeout=timeout)
        async with client:
            return await client.get_resource(uri)

    async def _default_log_handler(self, message: Any) -> None:
        """Default log handler for server messages."""
        if hasattr(message, 'data'):
            activity.logger.info(f"MCP Server: {message.data}")
        else:
            activity.logger.info(f"MCP Server: {message}")

    def _build_transport(
        self, server_def: MCPServerDefinition | Dict[str, Any] | None
    ) -> str | Dict[str, Any]:
        """Build transport specification from MCPServerDefinition or dict.
        
        This method builds the transport configuration but does NOT create
        or store any connections. Connections are managed by FastMCP's
        Client class within context managers.
        """
        if server_def is None:
            # Default to stdio connection with server.py
            return "server.py"

        # Handle both MCPServerDefinition objects and dicts (from Temporal)
        if isinstance(server_def, dict):
            conn_type = server_def.get("connection_type", "stdio")
            if conn_type == "http":
                # For HTTP, return the URL directly
                return server_def.get("url", "http://localhost:8000/mcp")
            else:
                # For stdio, check if it's a simple script path
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