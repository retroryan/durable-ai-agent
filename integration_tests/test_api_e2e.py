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
from models.trajectory import Trajectory


class MCPWeatherFlowTest:
    """Detailed test for consolidated MCP weather tool execution flow."""
    
    async def wait_for_agent_response(self, client: DurableAgentAPIClient, workflow_id: str, timeout: int = 60) -> bool:
        """Wait for agent response in conversation history."""
        max_attempts = timeout // 2
        for attempt in range(max_attempts):
            await asyncio.sleep(2)  # Poll every 2 seconds
            
            # Get conversation history
            history_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/history"
            )
            history_data = history_response.json()
            
            # Check if we have an agent response
            messages = history_data.get("conversation_history", [])
            if len(messages) >= 2 and messages[-1].get("role") == "agent":
                print(f"Got agent response after {(attempt + 1) * 2} seconds")
                return True
        
        print(f"❌ No agent response after {timeout} seconds")
        return False
    
    async def test_mcp_forecast_flow(self, client: DurableAgentAPIClient) -> bool:
        """Test the complete weather forecast tool flow (now always MCP)."""
        print("\n🌤️  Testing Consolidated Weather Forecast Tool Flow")
        print("=" * 60)
        
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        request = "What's the weather forecast for Seattle next week?"
        
        print(f"User: {user_name}")
        print(f"Request: {request}")
        print("\nExpected flow:")
        print("1. React agent selects get_weather_forecast tool")
        print("2. ToolExecutionActivity detects is_mcp=True")
        print("3. Routes internally to MCP client")
        print("4. Returns weather data")
        print("-" * 60)
        
        try:
            # Send request to start workflow
            initial_response = await client.chat(request, user_name=user_name)
            workflow_id = initial_response.get("workflow_id")
            
            if not workflow_id:
                print("❌ No workflow_id in response")
                return False
            
            print(f"Workflow started: {workflow_id}")
            
            # Poll for agent response
            print("Polling for agent response...")
            if not await self.wait_for_agent_response(client, workflow_id):
                return False
            
            # Get trajectories from API
            trajectories_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/ai-trajectories"
            )
            trajectories_data = trajectories_response.json()
            # Handle both list and dict response formats
            if isinstance(trajectories_data, dict):
                trajectories = trajectories_data.get("trajectories", [])
            elif isinstance(trajectories_data, list):
                trajectories = trajectories_data
            else:
                trajectories = []
            
            # Get conversation history for final message
            history_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/history"
            )
            history_data = history_response.json()
            messages = history_data.get("conversation_history", [])
            message = messages[-1].get("content", "") if messages else ""
            
            # Convert trajectory objects to steps for display
            steps = []
            for traj in trajectories:
                if isinstance(traj, dict):
                    step = {
                        "thought": traj.get("thought", ""),
                        "tool_name": traj.get("tool_name", ""),
                        "tool_args": traj.get("tool_args", {}),
                        "observation": traj.get("observation", "")
                    }
                else:
                    step = {
                        "thought": traj.thought,
                        "tool_name": traj.tool_name,
                        "tool_args": traj.tool_args,
                        "observation": traj.observation or ""
                    }
                steps.append(step)
            
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
                    print(f"   Observation: {step['observation'][:200]}...")
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
        request = "What are the agricultural conditions in Iowa for corn farming?"
        
        print(f"Request: {request}")
        
        try:
            # Start workflow
            initial_response = await client.chat(request, user_name=user_name)
            workflow_id = initial_response.get("workflow_id")
            
            if not workflow_id:
                print("❌ No workflow_id in response")
                return False
            
            # Poll for agent response
            if not await self.wait_for_agent_response(client, workflow_id):
                return False
            
            # Get trajectories from API
            trajectories_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/ai-trajectories"
            )
            trajectories_data = trajectories_response.json()
            # Handle both list and dict response formats
            if isinstance(trajectories_data, dict):
                trajectories = trajectories_data.get("trajectories", [])
            elif isinstance(trajectories_data, list):
                trajectories = trajectories_data
            else:
                trajectories = []
            
            # Check first tool used
            if trajectories:
                first_traj = trajectories[0]
                tool_name = first_traj.get("tool_name") if isinstance(first_traj, dict) else first_traj.tool_name
                
                if tool_name == "get_agricultural_conditions":
                    print("✅ Consolidated agricultural conditions tool used!")
                    
                    # Check for crop_type in args
                    tool_args = first_traj.get("tool_args") if isinstance(first_traj, dict) else first_traj.tool_args
                    if "crop_type" in tool_args and "corn" in str(tool_args.get("crop_type", "")).lower():
                        print("✅ Crop type (corn) correctly passed!")
                    
                    return True
                else:
                    print(f"❌ Expected get_agricultural_conditions but got: {tool_name}")
                    return False
            else:
                print("❌ No trajectories found")
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
        request = "What was the weather like in Chicago from 2025-01-01 to 2025-01-07?"
        
        print(f"Request: {request}")
        
        try:
            # Start workflow
            initial_response = await client.chat(request, user_name=user_name)
            workflow_id = initial_response.get("workflow_id")
            
            if not workflow_id:
                print("❌ No workflow_id in response")
                return False
            
            # Poll for agent response
            if not await self.wait_for_agent_response(client, workflow_id):
                return False
            
            # Get trajectories from API
            trajectories_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/ai-trajectories"
            )
            trajectories_data = trajectories_response.json()
            # Handle both list and dict response formats
            if isinstance(trajectories_data, dict):
                trajectories = trajectories_data.get("trajectories", [])
            elif isinstance(trajectories_data, list):
                trajectories = trajectories_data
            else:
                trajectories = []
            
            # Check first tool used
            if trajectories:
                first_traj = trajectories[0]
                tool_name = first_traj.get("tool_name") if isinstance(first_traj, dict) else first_traj.tool_name
                
                if tool_name == "get_historical_weather":
                    print("✅ Consolidated historical weather tool used!")
                    
                    # Check date args
                    tool_args = first_traj.get("tool_args") if isinstance(first_traj, dict) else first_traj.tool_args
                    if "start_date" in tool_args and "end_date" in tool_args:
                        print(f"✅ Date range passed: {tool_args['start_date']} to {tool_args['end_date']}")
                    
                    return True
                else:
                    print(f"❌ Expected get_historical_weather but got: {tool_name}")
                    return False
            else:
                print("❌ No trajectories found")
                return False
            
            return False
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    async def run_all_tests(self, client: DurableAgentAPIClient) -> int:
        """Run all MCP weather flow tests."""
        tests = [
            ("Weather Forecast Flow", self.test_mcp_forecast_flow),
            # ("Agricultural Conditions Flow", self.test_agricultural_conditions_flow),
            # ("Historical Weather Flow", self.test_historical_weather_flow),
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
    if not await client.health_check():
        print("❌ API is not healthy. Make sure services are running.")
        sys.exit(1)
    
    # Run tests
    failed = await test_suite.run_all_tests(client)
    
    # Exit with appropriate code
    sys.exit(failed)


if __name__ == "__main__":
    asyncio.run(main())