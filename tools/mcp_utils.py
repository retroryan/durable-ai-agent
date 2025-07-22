"""
Common utilities for MCP tool execution.

This module provides shared functionality for executing MCP tools
in an isolated async context from synchronous code.
"""
import asyncio
from typing import Any, Dict


def execute_mcp_sync(tool_instance, **kwargs) -> str:
    """
    Execute MCP tool using isolated async context.
    
    This function allows synchronous tools to execute MCP operations
    by creating an isolated async context. It handles the async/sync
    boundary in a clean, controlled manner.
    
    Args:
        tool_instance: The MCP tool instance (must have get_mcp_config method)
        **kwargs: Arguments to pass to the MCP tool
        
    Returns:
        str: The result from the MCP tool execution
    """
    async def _execute_async():
        from shared.mcp_client_manager import MCPClientManager
        
        manager = MCPClientManager()
        mcp_config = tool_instance.get_mcp_config()
        
        # Debug logging
        print(f"[DEBUG] Tool name being called: {mcp_config.tool_name}")
        print(f"[DEBUG] Server URL: {mcp_config.server_definition.url}")
        
        # Get or create client
        client = await manager.get_client(mcp_config.server_definition)
        
        # Call tool with wrapped arguments
        result = await client.call_tool(
            name=mcp_config.tool_name,
            arguments={"request": kwargs}
        )
        
        # Process result
        if hasattr(result, 'content'):
            return str(result.content[0].text if result.content else "No result")
        elif isinstance(result, list) and len(result) > 0:
            # Handle list of content items
            return str(result[0].text if hasattr(result[0], 'text') else result[0])
        else:
            return str(result)
    
    # Run async function in new event loop
    return asyncio.run(_execute_async())