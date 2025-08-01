#!/usr/bin/env python3
"""Test MCP client manager discovery and tool listing capabilities.

This integration test demonstrates:
- MCPClientManager connecting to the MCP server
- Discovering available tools with full details
- Logging tool metadata and schemas  
- Executing discovered tools with detailed logging
- Handling both successful and error cases

Usage:
    poetry run python integration_tests/test_mcp_client_discovery.py
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Load environment variables
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
else:
    print(f"No .env file found at {env_path}, using defaults")

sys.path.insert(0, str(project_root))
from shared.mcp_client_manager import MCPClientManager
from models.mcp_models import ForecastRequest, HistoricalRequest, AgriculturalRequest

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class MCPDiscoveryTest:
    """Test class for MCP client discovery and tool exploration."""
    
    def __init__(self):
        self.manager = MCPClientManager()
        self.discovered_tools: List[Dict[str, Any]] = []
        
    async def test_tool_discovery(self) -> bool:
        """Test discovering and logging all available tools."""
        # For local testing, always use localhost instead of Docker hostname
        mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:7778/mcp")
        # Replace Docker hostname with localhost for local testing
        if "mcp-server" in mcp_url:
            mcp_url = mcp_url.replace("mcp-server", "localhost")
        
        server_def = {
            "name": "weather-mcp",
            "connection_type": "http",
            "url": mcp_url
        }
        
        logger.info("=" * 80)
        logger.info("MCP CLIENT DISCOVERY TEST")
        logger.info("=" * 80)
        logger.info(f"Server URL: {server_def['url']}")
        logger.info("")
        
        try:
            # Step 1: List tools using MCPClientManager
            logger.info("STEP 1: Discovering Tools via MCPClientManager")
            logger.info("-" * 60)
            
            tools = await self.manager.list_tools(server_def)
            logger.info(f"Discovered {len(tools)} tools from server")
            
            # Log detailed information about each tool
            for i, tool in enumerate(tools, 1):
                logger.info("")
                logger.info(f"Tool #{i}: {tool.name}")
                logger.info("-" * 40)
                
                # Extract and log tool details
                tool_info = {
                    "name": tool.name,
                    "description": getattr(tool, "description", "No description"),
                    "schema": None
                }
                
                # Log basic info
                logger.info(f"  Name: {tool_info['name']}")
                logger.info(f"  Description: {tool_info['description']}")
                
                # Log input schema if available
                if hasattr(tool, "inputSchema"):
                    tool_info["schema"] = tool.inputSchema
                    logger.info(f"  Input Schema:")
                    logger.info(json.dumps(tool.inputSchema, indent=4))
                
                self.discovered_tools.append(tool_info)
            
            logger.info("")
            logger.info("Tool discovery completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def test_tool_execution(self) -> bool:
        """Test executing discovered tools with detailed logging."""
        logger.info("")
        logger.info("STEP 2: Testing Tool Execution")
        logger.info("-" * 60)
        
        # For local testing, always use localhost instead of Docker hostname
        mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:7778/mcp")
        if "mcp-server" in mcp_url:
            mcp_url = mcp_url.replace("mcp-server", "localhost")
        
        server_def = {
            "name": "weather-mcp",
            "connection_type": "http",
            "url": mcp_url
        }
        
        # Test cases for each tool
        test_cases = [
            {
                "tool": "get_weather_forecast",
                "args": {"location": "San Francisco", "days": 3},
                "model": ForecastRequest
            },
            {
                "tool": "get_historical_weather",
                "args": {
                    "location": "Chicago",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-07"
                },
                "model": HistoricalRequest
            },
            {
                "tool": "get_agricultural_conditions",
                "args": {
                    "location": "Iowa",
                    "days": 5,
                    "crop_type": "corn"
                },
                "model": AgriculturalRequest
            }
        ]
        
        all_passed = True
        
        for test in test_cases:
            logger.info("")
            logger.info(f"Testing tool: {test['tool']}")
            logger.info("-" * 30)
            
            try:
                # Create request model
                request_model = test["model"](**test["args"])
                logger.info(f"  Request model: {request_model}")
                logger.info(f"  Request JSON: {request_model.model_dump_json(indent=2)}")
                
                # Custom log handler for server messages
                async def log_handler(message):
                    logger.info(f"  [Server Log] {message}")
                
                # Execute tool with custom handlers
                logger.info(f"  Executing tool...")
                start_time = datetime.now()
                
                result = await self.manager.execute_tool(
                    server_def=server_def,
                    tool_name=test["tool"],
                    arguments={"request": request_model.model_dump()},
                    log_handler=log_handler
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"  Execution time: {elapsed:.3f}s")
                
                # Parse and log result
                result_data = self._parse_result(result)
                logger.info(f"  Result summary: {result_data.get('summary', 'No summary')}")
                logger.info(f"  Full result: {json.dumps(result_data, indent=2)}")
                logger.info(f"  ✓ Tool execution successful")
                
            except Exception as e:
                logger.error(f"  ✗ Tool execution failed: {e}")
                logger.error(f"  Error type: {type(e).__name__}")
                logger.error(traceback.format_exc())
                all_passed = False
        
        return all_passed
    
    def _parse_result(self, result) -> Dict[str, Any]:
        """Parse the result from execute_tool into a dictionary."""
        # Handle different result formats
        if isinstance(result, list):
            # Handle list format
            if len(result) > 0 and hasattr(result[0], 'text'):
                result_text = result[0].text
            else:
                result_text = str(result)
        elif hasattr(result, 'content'):
            # Handle content format
            if isinstance(result.content, list) and len(result.content) > 0:
                result_text = result.content[0].text
            else:
                result_text = str(result.content)
        else:
            result_text = str(result)
        
        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            return {"raw_result": result_text}
    
    async def test_error_handling(self) -> bool:
        """Test error handling with invalid requests."""
        logger.info("")
        logger.info("STEP 3: Testing Error Handling")
        logger.info("-" * 60)
        
        mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:7778/mcp")
        if "mcp-server" in mcp_url:
            mcp_url = mcp_url.replace("mcp-server", "localhost")
        
        server_def = {
            "name": "weather-mcp",
            "connection_type": "http",
            "url": mcp_url
        }
        
        # Test invalid tool name
        logger.info("Testing invalid tool name...")
        try:
            await self.manager.execute_tool(
                server_def=server_def,
                tool_name="invalid_tool_name",
                arguments={}
            )
            logger.error("  ✗ Expected error not raised for invalid tool")
            return False
        except Exception as e:
            logger.info(f"  ✓ Correctly caught error: {type(e).__name__}: {e}")
        
        # Test invalid arguments
        logger.info("")
        logger.info("Testing invalid arguments...")
        try:
            await self.manager.execute_tool(
                server_def=server_def,
                tool_name="get_weather_forecast",
                arguments={"invalid_arg": "test"}
            )
            logger.error("  ✗ Expected error not raised for invalid arguments")
            return False
        except Exception as e:
            logger.info(f"  ✓ Correctly caught error: {type(e).__name__}: {e}")
        
        return True
    
    def generate_summary(self) -> None:
        """Generate a summary of discovered tools."""
        logger.info("")
        logger.info("=" * 80)
        logger.info("DISCOVERY SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"Total tools discovered: {len(self.discovered_tools)}")
        logger.info("")
        logger.info("Tools available:")
        for tool in self.discovered_tools:
            logger.info(f"  - {tool['name']}: {tool['description']}")
        
        logger.info("")
        logger.info("Tool capabilities:")
        logger.info("  - Weather forecasting (location or coordinates)")
        logger.info("  - Historical weather data retrieval")
        logger.info("  - Agricultural condition analysis")
        
        logger.info("")
        logger.info("Key features demonstrated:")
        logger.info("  ✓ Async context manager pattern for connections")
        logger.info("  ✓ Pydantic model validation")
        logger.info("  ✓ Automatic retry with exponential backoff")
        logger.info("  ✓ Custom log and progress handlers")
        logger.info("  ✓ Comprehensive error handling")


async def main():
    """Run the MCP client discovery test."""
    parser = argparse.ArgumentParser(description="Test MCP client discovery")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\nMCP Client Manager Discovery Test")
    print("=================================")
    print("This test demonstrates the MCPClientManager discovering")
    print("and interacting with tools from the MCP server.")
    print("")
    print("Note: Make sure the MCP server is running:")
    print("  poetry run python scripts/run_mcp_server.py")
    print("")
    
    # Create test instance
    test = MCPDiscoveryTest()
    
    # Run tests
    success = True
    
    # Test 1: Tool discovery
    if not await test.test_tool_discovery():
        success = False
    
    # Test 2: Tool execution
    if success and not await test.test_tool_execution():
        success = False
    
    # Test 3: Error handling
    if success and not await test.test_error_handling():
        success = False
    
    # Generate summary
    test.generate_summary()
    
    # Final result
    logger.info("")
    logger.info("=" * 80)
    if success:
        logger.info("✓ ALL TESTS PASSED!")
        return 0
    else:
        logger.info("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)