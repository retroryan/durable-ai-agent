"""Tool and server definitions for MCP integration."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class MCPServerDefinition(BaseModel):
    """Definition for an MCP server connection."""

    name: str = Field(description="Name of the MCP server")
    connection_type: str = Field(
        default="stdio", description="Connection type: stdio or http"
    )
    command: str = Field(
        default="python", description="Command to run for stdio connections"
    )
    args: List[str] = Field(
        default_factory=lambda: ["server.py"], description="Arguments for the command"
    )
    env: Optional[Dict[str, str]] = Field(
        default=None, description="Environment variables"
    )
    url: Optional[str] = Field(default=None, description="URL for HTTP connections")
    included_tools: Optional[List[str]] = Field(
        default=None, description="List of tools to include"
    )
