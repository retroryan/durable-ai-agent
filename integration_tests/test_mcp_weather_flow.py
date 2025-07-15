#!/usr/bin/env python3
"""
Test MCP weather tool flow specifically with detailed trajectory analysis.
Run with: poetry run python integration_tests/test_mcp_weather_flow.py

This test focuses on verifying the complete MCP tool execution flow.
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime
from typing import Dict, Any

from utils.api_client import DurableAgentAPIClient


class MCPWeatherFlowTest:
    """Detailed test for MCP weather tool execution flow."""
    
    async def test_mcp_forecast_flow(self, client: DurableAgentAPIClient) -> bool:
        """Test the complete MCP forecast tool flow."""
        print("\n🌤️  Testing MCP Weather Forecast Flow")
        print("=" * 60)
        
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        request = "weather: What's the weather forecast for Seattle next week using the MCP forecast service?"
        
        print(f"User: {user_name}")
        print(f"Request: {request}")
        print("\nExpected flow:")
        print("1. React agent selects get_weather_forecast_mcp tool")
        print("2. Workflow routes to MCPExecutionActivity (300s timeout)")
        print("3. MCP client calls weather-proxy server")
        print("4. Returns mock forecast data")
        print("-" * 60)
        
        try:
            # Send request
            response = await client.chat(request, user_name=user_name)
            
            # Extract trajectory
            last_response = response.get("last_response", {})
            if isinstance(last_response, dict):
                trajectory = last_response.get("trajectory", {})
                message = last_response.get("message", "")
            else:
                print("❌ Unexpected response format")
                return False
            
            print("\n📊 Trajectory Analysis:")
            
            # Analyze each step
            steps = []
            i = 0
            while f"thought_{i}" in trajectory:
                step = {
                    "thought": trajectory.get(f"thought_{i}", ""),
                    "tool_name": trajectory.get(f"tool_name_{i}", ""),
                    "tool_args": trajectory.get(f"tool_args_{i}", {}),
                    "observation": trajectory.get(f"observation_{i}", "")
                }
                steps.append(step)
                i += 1
            
            # Print each step
            for idx, step in enumerate(steps):
                print(f"\n🔄 Step {idx + 1}:")
                print(f"   Thought: {step['thought'][:100]}...")
                print(f"   Tool: {step['tool_name']}")
                if step['tool_args']:
                    print(f"   Args: {json.dumps(step['tool_args'], indent=6)}")
                
                # Check if MCP tool was used
                if step['tool_name'].endswith('_mcp'):
                    print("   ✅ MCP tool detected!")
                    
                    # Check observation for mock data
                    obs_str = str(step['observation']).lower()
                    if '"mock": true' in obs_str or '"mock":true' in obs_str or 'mock weather' in obs_str:
                        print("   ✅ Mock data confirmed!")
                    else:
                        print("   ⚠️  Mock data not detected in observation")
            
            # Check final response
            print(f"\n📝 Final Response:")
            print(f"{message[:200]}...")
            
            # Verify MCP tool was used
            mcp_tools_used = [s['tool_name'] for s in steps if s['tool_name'].endswith('_mcp')]
            if 'get_weather_forecast_mcp' in mcp_tools_used:
                print("\n✅ MCP forecast tool successfully executed!")
                return True
            else:
                print(f"\n❌ Expected get_weather_forecast_mcp but got: {mcp_tools_used}")
                return False
                
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_mcp_tool_routing(self, client: DurableAgentAPIClient) -> bool:
        """Test that MCP tools are properly routed vs traditional tools."""
        print("\n🔀 Testing MCP Tool Routing")
        print("=" * 60)
        
        test_cases = [
            {
                "name": "Traditional Tool",
                "request": "weather: What's the weather forecast for Boston?",
                "expected_tool": "get_weather_forecast",
                "is_mcp": False
            },
            {
                "name": "MCP Tool (explicit)",
                "request": "weather: What's the weather forecast for Boston using the MCP service?",
                "expected_tool": "get_weather_forecast_mcp",
                "is_mcp": True
            }
        ]
        
        all_passed = True
        
        for test in test_cases:
            print(f"\n📍 {test['name']}")
            print(f"Request: {test['request']}")
            print(f"Expected: {test['expected_tool']} (MCP: {test['is_mcp']})")
            
            user_name = f"test_user_{uuid.uuid4().hex[:8]}"
            
            try:
                response = await client.chat(test['request'], user_name=user_name)
                
                # Extract tools used
                last_response = response.get("last_response", {})
                if isinstance(last_response, dict):
                    trajectory = last_response.get("trajectory", {})
                    
                    tools_used = []
                    for key, value in trajectory.items():
                        if key.startswith("tool_name_"):
                            tools_used.append(value)
                    
                    print(f"Tools used: {', '.join(tools_used)}")
                    
                    # Check if correct tool type was used
                    mcp_tools = [t for t in tools_used if t.endswith('_mcp')]
                    traditional_tools = [t for t in tools_used if not t.endswith('_mcp')]
                    
                    if test['is_mcp'] and mcp_tools:
                        print("✅ Correctly routed to MCP tool")
                    elif not test['is_mcp'] and traditional_tools and not mcp_tools:
                        print("✅ Correctly routed to traditional tool")
                    else:
                        print("❌ Incorrect routing")
                        all_passed = False
                        
            except Exception as e:
                print(f"❌ Test failed: {e}")
                all_passed = False
            
            await asyncio.sleep(1)
        
        return all_passed
    
    async def test_mcp_error_handling(self, client: DurableAgentAPIClient) -> bool:
        """Test MCP tool error handling."""
        print("\n⚠️  Testing MCP Error Handling")
        print("=" * 60)
        
        # This test would require a way to simulate MCP server errors
        # For now, we'll test with an edge case
        
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        request = "weather: Get forecast for coordinates 999.999, 999.999 using MCP service"
        
        print(f"Request: {request}")
        print("Expected: Graceful error handling")
        
        try:
            response = await client.chat(request, user_name=user_name)
            
            # Check if error was handled gracefully
            last_response = response.get("last_response", {})
            if isinstance(last_response, dict):
                message = last_response.get("message", "").lower()
                
                # In mock mode, this should still work
                if "forecast" in message or "weather" in message:
                    print("✅ Request handled gracefully")
                    return True
                else:
                    print("⚠️  Unexpected response")
                    return False
                    
        except Exception as e:
            print(f"❌ Unhandled error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all MCP weather flow tests."""
        print("🚀 Starting MCP Weather Flow Test")
        print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Check services
        import httpx
        try:
            response = httpx.get("http://localhost:8000/health", timeout=5.0)
            print("✅ API server is running")
        except Exception:
            print("❌ API server not accessible")
            print("Run: TOOLS_MOCK=true docker-compose --profile weather_proxy up")
            return 1
        
        results = {
            "passed": 0,
            "failed": 0
        }
        
        async with DurableAgentAPIClient() as client:
            # Test 1: MCP Forecast Flow
            if await self.test_mcp_forecast_flow(client):
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            await asyncio.sleep(2)
            
            # Test 2: Tool Routing
            if await self.test_mcp_tool_routing(client):
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            await asyncio.sleep(2)
            
            # Test 3: Error Handling
            if await self.test_mcp_error_handling(client):
                results["passed"] += 1
            else:
                results["failed"] += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 Test Summary:")
        print(f"   ✅ Passed: {results['passed']}/3")
        print(f"   ❌ Failed: {results['failed']}/3")
        
        if results["failed"] == 0:
            print("\n🎉 All MCP weather flow tests passed!")
            return 0
        else:
            return 1


async def main():
    """Main entry point."""
    test = MCPWeatherFlowTest()
    return await test.run_all_tests()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)