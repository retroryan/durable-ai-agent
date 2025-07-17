#!/usr/bin/env python3
"""
Test consolidated MCP weather tool flow with detailed trajectory analysis.
Run with: poetry run python integration_tests/test_mcp_weather_flow.py

This test focuses on verifying the complete MCP tool execution flow with consolidated tools.
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime
from typing import Dict, Any

from utils.api_client import DurableAgentAPIClient


class MCPWeatherFlowTest:
    """Detailed test for consolidated MCP weather tool execution flow."""
    
    async def test_mcp_forecast_flow(self, client: DurableAgentAPIClient) -> bool:
        """Test the complete weather forecast tool flow (now always MCP)."""
        print("\n🌤️  Testing Consolidated Weather Forecast Tool Flow")
        print("=" * 60)
        
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        request = "weather: What's the weather forecast for Seattle next week?"
        
        print(f"User: {user_name}")
        print(f"Request: {request}")
        print("\nExpected flow:")
        print("1. React agent selects get_weather_forecast tool")
        print("2. ToolExecutionActivity detects is_mcp=True")
        print("3. Routes internally to MCP client")
        print("4. Returns weather data")
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
            
            # Parse trajectory steps
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
                
                # Check if consolidated tool was used (no _mcp suffix)
                if step['tool_name'] == 'get_weather_forecast':
                    print("   ✅ Consolidated weather forecast tool detected!")
                    
                    # Check observation for data
                    obs_str = str(step['observation']).lower()
                    if 'weather' in obs_str or 'forecast' in obs_str or 'temperature' in obs_str:
                        print("   ✅ Weather data received!")
                    else:
                        print("   ⚠️  Weather data not detected in observation")
            
            # Check final response
            print(f"\n📝 Final Response:")
            print(f"{message[:200]}...")
            
            # Verify consolidated tool was used
            tools_used = [s['tool_name'] for s in steps]
            if 'get_weather_forecast' in tools_used:
                print("\n✅ Consolidated weather forecast tool successfully executed!")
                # Verify no _mcp suffix tools were used
                mcp_suffix_tools = [t for t in tools_used if t.endswith('_mcp')]
                if mcp_suffix_tools:
                    print(f"❌ Found unexpected _mcp suffix tools: {mcp_suffix_tools}")
                    return False
                return True
            else:
                print(f"\n❌ Expected get_weather_forecast but got: {tools_used}")
                return False
                
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_agricultural_conditions_flow(self, client: DurableAgentAPIClient) -> bool:
        """Test agricultural conditions tool (consolidated MCP)."""
        print("\n🌾 Testing Agricultural Conditions Tool")
        print("=" * 60)
        
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        request = "weather: What are the agricultural conditions in Iowa for corn farming?"
        
        print(f"Request: {request}")
        
        try:
            response = await client.chat(request, user_name=user_name)
            last_response = response.get("last_response", {})
            
            if isinstance(last_response, dict):
                trajectory = last_response.get("trajectory", {})
                
                # Check first tool used
                tool_name = trajectory.get("tool_name_0", "")
                if tool_name == "get_agricultural_conditions":
                    print("✅ Consolidated agricultural conditions tool used!")
                    
                    # Check for crop_type in args
                    tool_args = trajectory.get("tool_args_0", {})
                    if "crop_type" in tool_args and "corn" in str(tool_args.get("crop_type", "")).lower():
                        print("✅ Crop type (corn) correctly passed!")
                    
                    return True
                else:
                    print(f"❌ Expected get_agricultural_conditions but got: {tool_name}")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    async def test_historical_weather_flow(self, client: DurableAgentAPIClient) -> bool:
        """Test historical weather tool (consolidated MCP)."""
        print("\n📊 Testing Historical Weather Tool")
        print("=" * 60)
        
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        request = "weather: What was the weather like in Chicago from 2025-01-01 to 2025-01-07?"
        
        print(f"Request: {request}")
        
        try:
            response = await client.chat(request, user_name=user_name)
            last_response = response.get("last_response", {})
            
            if isinstance(last_response, dict):
                trajectory = last_response.get("trajectory", {})
                
                # Check first tool used
                tool_name = trajectory.get("tool_name_0", "")
                if tool_name == "get_historical_weather":
                    print("✅ Consolidated historical weather tool used!")
                    
                    # Check date args
                    tool_args = trajectory.get("tool_args_0", {})
                    if "start_date" in tool_args and "end_date" in tool_args:
                        print(f"✅ Date range passed: {tool_args['start_date']} to {tool_args['end_date']}")
                    
                    return True
                else:
                    print(f"❌ Expected get_historical_weather but got: {tool_name}")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    async def run_all_tests(self, client: DurableAgentAPIClient) -> int:
        """Run all MCP weather flow tests."""
        tests = [
            ("Weather Forecast Flow", self.test_mcp_forecast_flow),
            ("Agricultural Conditions Flow", self.test_agricultural_conditions_flow),
            ("Historical Weather Flow", self.test_historical_weather_flow),
        ]
        
        passed = 0
        failed = 0
        
        print("\n" + "=" * 60)
        print("🧪 Running Consolidated MCP Weather Tool Tests")
        print("=" * 60)
        
        for test_name, test_func in tests:
            try:
                if await test_func(client):
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"\n❌ {test_name} crashed: {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        print("=" * 60)
        
        return failed


async def main():
    """Run the MCP weather flow tests."""
    client = DurableAgentAPIClient()
    test_suite = MCPWeatherFlowTest()
    
    # Check API health
    if not await client.check_health():
        print("❌ API is not healthy. Make sure services are running.")
        sys.exit(1)
    
    # Run tests
    failed = await test_suite.run_all_tests(client)
    
    # Exit with appropriate code
    sys.exit(failed)


if __name__ == "__main__":
    asyncio.run(main())