#!/usr/bin/env python3
"""
Integration test for MCP tools using direct tool execution.
Run with: poetry run python integration_tests/test_mcp_tools_direct.py
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from shared.tool_utils.registry import create_tool_set_registry
from shared.mcp_client_manager import MCPClientManager
from shared.tool_utils.agriculture_tool_set import AgricultureToolSet

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_tools():
    """Test MCP tools directly using the MCP client manager."""
    print("🚀 Starting Direct MCP Tools Integration Test")
    print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Create tool registry
    tool_set_name = os.getenv("TOOL_SET", "agriculture")
    tools_mock = os.getenv("TOOLS_MOCK", "false").lower() == "true"
    
    print(f"\n📦 Creating tool registry for: {tool_set_name}")
    print(f"🔧 Mock mode: {tools_mock}")
    
    registry = create_tool_set_registry(tool_set_name, mock_results=tools_mock)
    mcp_client_manager = MCPClientManager()
    
    # Get test cases
    test_cases = AgricultureToolSet.get_test_cases()
    # All agriculture tools are now MCP-enabled (no _mcp suffix needed)
    mcp_test_cases = test_cases
    
    print(f"\n📊 Running {len(mcp_test_cases)} test cases (all tools are MCP-enabled)")
    print("=" * 60)
    
    successful_tests = 0
    failed_tests = 0
    
    for i, test_case in enumerate(mcp_test_cases, 1):
        print(f"\n📍 Test {i}/{len(mcp_test_cases)}: {test_case.description}")
        print(f"🎯 Scenario: {test_case.scenario}")
        print(f"🔧 Expected tools: {', '.join(test_case.expected_tools)}")
        print("-" * 40)
        
        # Test each expected tool (all are MCP-enabled)
        for tool_name in test_case.expected_tools:
            print(f"\n🔨 Testing tool: {tool_name}")
            
            try:
                # Get the tool from registry
                tool = registry.get_tool(tool_name)
                if not tool:
                    print(f"❌ Tool not found in registry: {tool_name}")
                    print(f"   Available tools: {registry.get_tool_names()}")
                    failed_tests += 1
                    continue
                
                # Get MCP configuration
                mcp_config = tool.get_mcp_config()
                print(f"📡 MCP Server: {mcp_config.server_definition.name}")
                print(f"🔌 MCP Tool: {mcp_config.tool_name}")
                
                # Get or create MCP client
                client = await mcp_client_manager.get_client(mcp_config.server_definition)
                
                # Prepare test arguments based on the tool
                test_args = {}
                if 'forecast' in tool_name:
                    test_args = {
                        "location": "San Francisco, CA",
                        "days": 3
                    }
                elif 'historical' in tool_name:
                    test_args = {
                        "location": "Chicago, IL",
                        "start_date": "2024-01-01",
                        "end_date": "2024-01-07"
                    }
                elif 'agricultural' in tool_name:
                    test_args = {
                        "location": "Iowa City, IA",
                        "crop_type": "corn"
                    }
                
                print(f"📤 Sending args: {json.dumps(test_args, indent=2)}")
                
                # Call the MCP tool - wrap args in 'request' for proxy compatibility
                wrapped_args = {"request": test_args}
                result = await client.call_tool(
                    name=mcp_config.tool_name,
                    arguments=wrapped_args
                )
                
                # Process result
                if hasattr(result, 'content'):
                    observation = result.content[0].text if result.content else "No result"
                else:
                    observation = str(result)
                
                print(f"\n📥 Result:")
                # Try to parse as JSON for better formatting
                try:
                    result_data = json.loads(observation)
                    print(json.dumps(result_data, indent=2))
                except:
                    print(observation[:500] + "..." if len(observation) > 500 else observation)
                
                print(f"✅ Tool {tool_name} executed successfully!")
                successful_tests += 1
                
            except Exception as e:
                print(f"❌ Failed to execute tool {tool_name}: {e}")
                logger.error(f"Tool execution error", exc_info=True)
                failed_tests += 1
            
            # Small delay between tool calls
            await asyncio.sleep(0.5)
    
    # Cleanup
    await mcp_client_manager.cleanup()
    
    print("\n" + "=" * 60)
    print(f"✨ Test completed! Results:")
    print(f"   ✅ Successful: {successful_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 All MCP tool tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed")
        return 1


def check_services():
    """Check if required MCP services are running."""
    import httpx
    
    print("🔍 Checking MCP services...")
    
    services_to_check = [
        {"name": "Weather Proxy", "url": "http://localhost:8001/mcp/", "required": True},
        {"name": "Forecast Service", "url": "http://localhost:7778/mcp", "required": False},
        {"name": "Historical Service", "url": "http://localhost:7779/mcp", "required": False},
        {"name": "Agricultural Service", "url": "http://localhost:7780/mcp", "required": False},
    ]
    
    all_good = True
    
    for service in services_to_check:
        try:
            response = httpx.get(service["url"], timeout=5.0)
            # MCP servers require text/event-stream accept header, so 406 is expected
            if response.status_code in [200, 406, 307]:
                print(f"✅ {service['name']} is running at {service['url']}")
            else:
                print(f"⚠️  {service['name']} returned status {response.status_code}")
                if service["required"]:
                    all_good = False
        except Exception as e:
            print(f"❌ {service['name']} is not accessible at {service['url']}")
            if service["required"]:
                all_good = False
    
    if not all_good:
        print("\n💡 Make sure to run one of:")
        print("   docker-compose --profile weather_proxy up  (recommended)")
        print("   docker-compose --profile forecast up       (individual services)")
        return False
    
    return True


if __name__ == "__main__":
    print("🏗️  Durable AI Agent - Direct MCP Tools Test")
    print("=" * 60)
    
    # Check if services are running
    if not check_services():
        print("\n⚠️  Please start the MCP services before running this test.")
        sys.exit(1)
    
    print("")
    
    # Run the async main function
    try:
        exit_code = asyncio.run(test_mcp_tools())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        logger.error("Test failed", exc_info=True)
        sys.exit(1)