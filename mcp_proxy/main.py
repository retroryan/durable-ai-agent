"""
MCP Proxy Server - Simple unified interface for multiple MCP weather servers.

This is a DEMO implementation focusing on simplicity and clarity.
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from mcp_proxy.services.manager import WeatherServiceManager


# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service manager
service_manager: WeatherServiceManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - start/stop services."""
    global service_manager
    
    logger.info("Starting MCP Proxy Server...")
    
    # Initialize service manager
    service_manager = WeatherServiceManager()
    
    # Start all services
    await service_manager.start_all()
    logger.info("All weather services started successfully")
    
    yield
    
    # Shutdown services
    logger.info("Shutting down MCP Proxy Server...")
    if service_manager:
        await service_manager.shutdown()
    logger.info("All services shut down")


# Create FastAPI app
app = FastAPI(
    title="MCP Weather Proxy",
    version="1.0.0",
    description="Simple proxy for MCP weather services",
    lifespan=lifespan
)


@app.post("/mcp/{service_name}")
async def proxy_mcp_request(service_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Proxy MCP requests to the appropriate weather service.
    
    Each request gets a fresh session automatically via FastMCP.as_proxy().
    
    Args:
        service_name: Name of the service (forecast, current, historical)
        request: MCP protocol request
    
    Returns:
        MCP protocol response
    """
    if not service_manager:
        raise HTTPException(500, "Service manager not initialized")
    
    proxy = service_manager.get_proxy(service_name)
    if not proxy:
        raise HTTPException(404, f"Service '{service_name}' not found")
    
    try:
        # For this demo, we'll handle the request directly through the proxy's methods
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id", 1)
        
        if method == "tools/list":
            # List available tools through the tool manager
            try:
                tools = await proxy._tool_manager.list_tools()
                # Convert tools to MCP format
                mcp_tools = []
                for tool in tools:
                    mcp_tool = tool.to_mcp_tool()
                    mcp_tools.append(mcp_tool.model_dump())
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": mcp_tools
                    }
                }
            except Exception as e:
                logger.error(f"Error listing tools: {e}", exc_info=True)
                raise
        elif method == "tools/call":
            # Call a specific tool through the tool manager
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result = await proxy._tool_manager.call_tool(tool_name, arguments)
            # Convert ToolResult to MCP format
            mcp_result = result.to_mcp_result()
            if isinstance(mcp_result, tuple):
                content, structured = mcp_result
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content,
                        "structuredContent": structured
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": mcp_result
                    }
                }
        else:
            # Method not supported
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    except Exception as e:
        logger.error(f"Error handling request for {service_name}: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Simple health check endpoint."""
    if not service_manager:
        return {
            "status": "unhealthy",
            "reason": "Service manager not initialized"
        }
    
    services_status = await service_manager.health_check()
    all_healthy = all(services_status.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "services": services_status
    }


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with basic info."""
    return {
        "name": "MCP Weather Proxy",
        "version": "1.0.0",
        "services": ["forecast", "current", "historical"],
        "endpoints": {
            "proxy": "/mcp/{service_name}",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("MCP_PROXY_PORT", 8000))
    logger.info(f"Starting MCP Proxy Server on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)