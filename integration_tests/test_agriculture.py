#!/usr/bin/env python3
"""
Integration tests for agriculture tool use cases.
Run with: poetry run python integration_tests/test_agriculture.py

This test verifies all agriculture tool use cases by sending queries to the API server.

Usage:
    poetry run python integration_tests/test_agriculture.py          # Run all tests
    poetry run python integration_tests/test_agriculture.py 2        # Run first 2 tests
    poetry run python integration_tests/test_agriculture.py 1        # Run only first test
    poetry run python integration_tests/test_agriculture.py -d       # Run with detailed output
    poetry run python integration_tests/test_agriculture.py -d 2     # Run first 2 tests with detailed output
"""
import argparse
import asyncio
import json
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from utils.api_client import DurableAgentAPIClient


class AgricultureIntegrationTest:
    """Integration tests for agriculture tool use cases."""
    
    def __init__(self, detailed: bool = False):
        """Initialize test suite with optional detailed output mode."""
        self.detailed = detailed
    
    async def wait_for_agent_response(self, client: DurableAgentAPIClient, workflow_id: str, timeout: int = 60) -> Tuple[bool, float]:
        """Wait for agent response with optional progress indicators."""
        start_time = time.time()
        max_attempts = timeout // 2
        
        if self.detailed:
            print("⏳ Waiting for agent response", end="", flush=True)
        
        for attempt in range(max_attempts):
            await asyncio.sleep(2)  # Poll every 2 seconds
            if self.detailed:
                print(".", end="", flush=True)
            
            # Use /status endpoint like the frontend does
            status_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/status"
            )
            status_data = status_response.json()
            
            # Check conversation_history if present (same as frontend)
            conversation_history = status_data.get("conversation_history", [])
            if conversation_history:
                # Look for agent messages
                for msg in conversation_history:
                    if msg.get("role") == "agent":
                        elapsed = time.time() - start_time
                        if self.detailed:
                            print(f"\n✅ Got agent response after {elapsed:.2f} seconds")
                            print(f"   Status: {status_data.get('status')}")
                            print(f"   Messages in history: {len(conversation_history)}")
                        else:
                            print(f"✅ Got agent response after {(attempt + 1) * 2} seconds")
                        return True, elapsed
            
            # Also check last_response for compatibility
            last_response = status_data.get("last_response", {})
            if last_response and last_response.get("message") != "Processing your request...":
                elapsed = time.time() - start_time
                if self.detailed:
                    print(f"\n✅ Got agent response after {elapsed:.2f} seconds")
                else:
                    print(f"✅ Got agent response after {(attempt + 1) * 2} seconds")
                return True, elapsed
        
        elapsed = time.time() - start_time
        print(f"\n❌ No agent response after {timeout} seconds")
        return False, elapsed
    
    def format_trajectory_step(self, trajectory: Dict[str, Any], index: int) -> str:
        """Format a single trajectory step for display."""
        output = []
        output.append(f"\n{'─' * 60}")
        output.append(f"🔄 Iteration {index}")
        output.append(f"{'─' * 60}")
        
        # Thought
        thought = trajectory.get("thought", "")
        output.append(f"💭 Thought:")
        output.append(f"   {thought}")
        
        # Action (Tool selection)
        tool_name = trajectory.get("tool_name", "")
        tool_args = trajectory.get("tool_args", {})
        output.append(f"\n🔧 Action: {tool_name}")
        if tool_args:
            output.append(f"   Arguments:")
            for key, value in tool_args.items():
                output.append(f"     - {key}: {value}")
        
        # Observation
        observation = trajectory.get("observation", "")
        if observation:
            output.append(f"\n👁️  Observation:")
            # Truncate very long observations
            if len(str(observation)) > 500:
                output.append(f"   {str(observation)[:500]}...")
                output.append(f"   [Truncated - {len(str(observation))} total characters]")
            else:
                output.append(f"   {observation}")
        
        # Error (if any)
        error = trajectory.get("error", "")
        if error:
            output.append(f"\n❌ Error: {error}")
        
        return "\n".join(output)
    
    async def query_workflow_details(self, client: DurableAgentAPIClient, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Query workflow for comprehensive execution details."""
        try:
            response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/query"
            )
            if response.status_code == 200:
                return response.json()
            
            status_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/workflow-status"
            )
            if status_response.status_code == 200:
                return status_response.json()
                
            return None
        except Exception as e:
            if self.detailed:
                print(f"⚠️  Could not query workflow details: {e}")
            return None
    
    async def run_test_case(self, client: DurableAgentAPIClient, query: str, test_name: str, test_number: int = None, total_tests: int = None) -> Dict[str, Any]:
        """Run a single test case and return results."""
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        
        if self.detailed and test_number and total_tests:
            # Detailed test header
            print(f"\n{'='*80}")
            print(f"{'🧪 Test Case ' + str(test_number) + '/' + str(total_tests):^80}")
            print(f"{'='*80}")
            print(f"📋 Test Name: {test_name}")
            print(f"📤 Query: {query}")
            print(f"👤 User: {user_name}")
            print(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("─" * 80)
        else:
            # Simple test header
            print(f"\n{'='*80}")
            print(f"🧪 TEST: {test_name}")
            print(f"{'='*80}")
            print(f"📤 Query: {query}")
            print("-" * 80)
        
        try:
            # Send request to start workflow
            if self.detailed:
                print("\n▶️  Starting workflow...")
            start_time = time.time()
            initial_response = await client.chat(query, user_name=user_name)
            workflow_id = initial_response.get("workflow_id")
            
            if not workflow_id:
                print("❌ No workflow_id in response")
                return {"success": False, "error": "No workflow_id"}
            
            print(f"✅ Workflow started: {workflow_id}")
            
            # Poll for agent response
            if self.detailed:
                print("\n" + "─" * 60)
                print("🔄 React Agent Execution")
                print("─" * 60)
            else:
                print("⏳ Polling for agent response...")
            
            success, response_time = await self.wait_for_agent_response(client, workflow_id)
            if not success:
                return {"success": False, "error": "No agent response"}
            
            # Query workflow details if in detailed mode
            if self.detailed:
                workflow_details = await self.query_workflow_details(client, workflow_id)
                if workflow_details:
                    print(f"\n📊 Workflow Details:")
                    print(f"   - Status: {workflow_details.get('status', 'unknown')}")
                    print(f"   - Message Count: {workflow_details.get('message_count', 0)}")
                    print(f"   - Interaction Count: {workflow_details.get('interaction_count', 0)}")
            
            # Get trajectories from API
            if self.detailed:
                print("\n" + "─" * 60)
                print("📍 Trajectory Analysis")
                print("─" * 60)
            
            trajectories_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/ai-trajectories"
            )
            trajectories_data = trajectories_response.json()
            
            # Handle both list and dict response formats
            if isinstance(trajectories_data, dict):
                trajectories = trajectories_data.get("trajectories", [])
                summary = trajectories_data.get("summary", "")
            else:
                trajectories = trajectories_data if isinstance(trajectories_data, list) else []
                summary = ""
            
            # Display trajectory summary if in detailed mode
            if self.detailed and summary:
                print(f"\n📈 Summary: {summary}")
            
            # Get final response (use status endpoint to match frontend)
            if self.detailed:
                print("\n" + "─" * 60)
                print("📝 Extract Agent")
                print("─" * 60)
            
            # Get final status to match frontend behavior
            final_status_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/status"
            )
            final_status_data = final_status_response.json()
            
            # Try to get message from conversation_history first (like frontend)
            final_message = ""
            conversation_history = final_status_data.get("conversation_history", [])
            if conversation_history:
                # Find last agent message
                for msg in reversed(conversation_history):
                    if msg.get("role") == "agent":
                        final_message = msg.get("content", "")
                        break
            
            # Fallback to last_response if no conversation history
            if not final_message:
                last_response = final_status_data.get("last_response", {})
                final_message = last_response.get("message", "")
            
            if self.detailed:
                print("✅ Answer extracted successfully")
            
            # Extract tools used and display trajectories if detailed
            tools_used = []
            for i, traj in enumerate(trajectories, 1):
                if isinstance(traj, dict):
                    if self.detailed:
                        print(self.format_trajectory_step(traj, i))
                    if traj.get("tool_name"):
                        tools_used.append({
                            "name": traj["tool_name"],
                            "args": traj.get("tool_args", {})
                        })
                else:
                    # Handle Trajectory object
                    traj_dict = {
                        "thought": traj.thought,
                        "tool_name": traj.tool_name,
                        "tool_args": traj.tool_args,
                        "observation": traj.observation,
                        "error": traj.error if hasattr(traj, 'error') else None
                    }
                    if self.detailed:
                        print(self.format_trajectory_step(traj_dict, i))
                    if traj.tool_name:
                        tools_used.append({
                            "name": traj.tool_name,
                            "args": traj.tool_args
                        })
            
            # Display results based on mode
            if self.detailed:
                print("\n" + "─" * 60)
                print("📊 Results")
                print("─" * 60)
                
                total_time = time.time() - start_time
                print(f"⏱️  Total execution time: {total_time:.2f}s")
                print(f"🔧 Tools used: {', '.join([t['name'] for t in tools_used])}")
                print(f"🔄 React iterations: {len(trajectories)}")
                
                # Display final answer
                print("\n" + "─" * 60)
                print("🎯 Final Answer")
                print("─" * 60)
                print(final_message)
                print("─" * 60)
            else:
                # Simple output for non-detailed mode
                if tools_used:
                    print(f"\n🔧 Tools Used:")
                    print("-" * 40)
                    for i, tool in enumerate(tools_used, 1):
                        print(f"{i}. Tool: {tool['name']}")
                        if tool['args']:
                            print(f"   Args: {json.dumps(tool['args'], indent=6)}")
                    print("-" * 40)
                
                # Check final response
                print(f"\n📝 Final Response:")
                print("=" * 60)
                print(final_message)
                print("=" * 60)
            
            return {
                "success": True,
                "tools_used": tools_used,
                "final_message": final_message,
                "workflow_id": workflow_id,
                "execution_time": total_time if self.detailed else None,
                "iterations": len(trajectories),
                "trajectories": trajectories if self.detailed else None
            }
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def test_multi_location_comparison(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test multi-location weather and agricultural comparison for grape growing."""
        result = await self.run_test_case(
            client,
            "Compare current weather and agricultural conditions between Napa Valley and Sonoma County for grape growing. Which location has better conditions right now?",
            "Multi-Location Grape Growing Comparison",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            # Agent efficiently uses only agricultural conditions for both locations
            forecast_count = tools.count("get_weather_forecast")
            agricultural_count = tools.count("get_agricultural_conditions")
            
            print(f"📊 Tools summary: {forecast_count} weather forecasts, {agricultural_count} agricultural conditions")
            print(f"🔄 Total iterations: {result.get('iterations', 'unknown')}")
            
            # Verify we got agricultural conditions for both locations
            total_tools = len([t for t in tools if t != "finish"])
            if agricultural_count >= 2:
                print(f"✅ Agricultural conditions tool used {agricultural_count} times")
                print(f"✅ Total of {total_tools} tool calls made")
                
                # Check if both locations were analyzed
                napa_checked = False
                sonoma_checked = False
                
                for tool in result["tools_used"]:
                    if tool["name"] == "get_agricultural_conditions":
                        args = tool["args"]
                        lat = args.get('latitude', '')
                        lon = args.get('longitude', '')
                        # Napa Valley coordinates: ~38.50, -122.26
                        if "38.5" in str(lat) or "38.50" in str(lat):
                            napa_checked = True
                        # Sonoma County coordinates: ~38.44, -122.71
                        elif "38.4" in str(lat) or "38.44" in str(lat):
                            sonoma_checked = True
                
                if napa_checked and sonoma_checked:
                    print("✅ Both Napa Valley and Sonoma County analyzed")
                    return True
                else:
                    if not napa_checked:
                        print("❌ Napa Valley not properly analyzed")
                    if not sonoma_checked:
                        print("❌ Sonoma County not properly analyzed")
                    return False
            else:
                print(f"❌ Expected at least 2 agricultural conditions calls")
                print(f"   Got: {total_tools} total tools, {agricultural_count} agricultural")
                print(f"   All tools used: {tools}")
                return False
        return False
    
    async def test_weather_forecast_basic(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test basic weather forecast request."""
        result = await self.run_test_case(
            client,
            "What's the weather forecast for New York City?",
            "Basic Weather Forecast",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            if "get_weather_forecast" in tools:
                print("✅ Weather forecast tool used correctly")
                return True
            else:
                print(f"❌ Expected get_weather_forecast but got: {tools}")
                return False
        return False
    
    async def test_weather_forecast_with_recommendation(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test weather forecast with umbrella recommendation."""
        result = await self.run_test_case(
            client,
            "What's the weather like in New York and should I bring an umbrella?",
            "Weather Forecast with Recommendation",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            if "get_weather_forecast" in tools:
                print("✅ Weather forecast tool used correctly")
                # Check if response mentions umbrella
                if "umbrella" in result["final_message"].lower():
                    print("✅ Response includes umbrella recommendation")
                return True
            else:
                print(f"❌ Expected get_weather_forecast but got: {tools}")
                return False
        return False
    
    async def test_10_day_forecast(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test 10-day weather forecast."""
        result = await self.run_test_case(
            client,
            "I need the 10-day weather forecast for London",
            "10-Day Weather Forecast",
            test_num,
            total
        )
        
        if result["success"]:
            tools_used = result["tools_used"]
            if tools_used and tools_used[0]["name"] == "get_weather_forecast":
                print("✅ Weather forecast tool used")
                # Check if days parameter was passed
                args = tools_used[0]["args"]
                if "days" in args and args["days"] == 10:
                    print("✅ 10-day parameter passed correctly")
                return True
            else:
                print(f"❌ Expected get_weather_forecast")
                return False
        return False
    
    async def test_multi_timeframe_forecast(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test weather forecast across multiple timeframes."""
        result = await self.run_test_case(
            client,
            "I need the 3-day, 7-day, and 10-day weather forecasts for Chicago to plan different farm activities. Give me a summary of each timeframe.",
            "Multi-Timeframe Weather Forecast",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            # Agent efficiently uses a single 10-day forecast to provide all timeframes
            forecast_count = tools.count("get_weather_forecast")
            total_tools = len([t for t in tools if t != "finish"])
            
            print(f"📊 Tools summary: {forecast_count} weather forecasts")
            print(f"🔄 Total iterations: {result.get('iterations', 'unknown')}")
            
            # Verify the agent used weather forecast and got 10-day data
            if forecast_count >= 1:
                print(f"✅ Weather forecast tool used {forecast_count} times")
                print(f"✅ Total of {total_tools} tool calls made")
                
                # Check if 10-day forecast was requested (which includes all timeframes)
                got_10_day = False
                
                for tool in result["tools_used"]:
                    if tool["name"] == "get_weather_forecast":
                        args = tool["args"]
                        days = args.get('days', 7)  # Default is 7
                        if days == 10:
                            got_10_day = True
                            print(f"✅ 10-day forecast requested (includes 3-day and 7-day data)")
                
                # Check if the response mentions all three timeframes
                response = result.get("final_message", "").lower()
                has_3_day = "3-day" in response or "3 day" in response
                has_7_day = "7-day" in response or "7 day" in response
                has_10_day = "10-day" in response or "10 day" in response
                
                if got_10_day and has_3_day and has_7_day and has_10_day:
                    print("✅ All three timeframes analyzed from single 10-day forecast")
                    return True
                else:
                    if not got_10_day:
                        print("❌ 10-day forecast not requested")
                    if not has_3_day:
                        print("❌ 3-day summary not provided in response")
                    if not has_7_day:
                        print("❌ 7-day summary not provided in response")
                    if not has_10_day:
                        print("❌ 10-day summary not provided in response")
                    return False
            else:
                print(f"❌ Expected at least 1 forecast call")
                print(f"   Got: {forecast_count} forecast calls, {total_tools} total tools")
                print(f"   All tools used: {tools}")
                return False
        return False
    
    async def test_agricultural_conditions_basic(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test agricultural conditions request."""
        result = await self.run_test_case(
            client,
            "What are the agricultural conditions in Des Moines, Iowa?",
            "Agricultural Conditions",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            if "get_agricultural_conditions" in tools:
                print("✅ Agricultural conditions tool used correctly")
                return True
            else:
                print(f"❌ Expected get_agricultural_conditions but got: {tools}")
                return False
        return False
    
    async def test_agricultural_with_crop(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test agricultural conditions with specific crop."""
        result = await self.run_test_case(
            client,
            "Are conditions good for planting corn in Ames, Iowa?",
            "Agricultural Conditions for Corn",
            test_num,
            total
        )
        
        if result["success"]:
            tools_used = result["tools_used"]
            if tools_used and tools_used[0]["name"] == "get_agricultural_conditions":
                print("✅ Agricultural conditions tool used")
                # Check if crop_type was passed
                args = tools_used[0]["args"]
                if "crop_type" in args and "corn" in str(args["crop_type"]).lower():
                    print("✅ Crop type (corn) passed correctly")
                return True
            else:
                print(f"❌ Expected get_agricultural_conditions")
                return False
        return False
    
    async def test_tree_farm_conditions(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test agricultural conditions for tree farm."""
        result = await self.run_test_case(
            client,
            "What are the soil moisture levels at my tree farm in Olympia, Washington?",
            "Tree Farm Conditions",
            test_num,
            total
        )
        
        if result["success"]:
            tools_used = result["tools_used"]
            if tools_used and tools_used[0]["name"] == "get_agricultural_conditions":
                print("✅ Agricultural conditions tool used")
                # Check if crop_type was passed
                args = tools_used[0]["args"]
                if "crop_type" in args and "tree" in str(args["crop_type"]).lower():
                    print("✅ Crop type (trees) passed correctly")
                return True
            else:
                print(f"❌ Expected get_agricultural_conditions")
                return False
        return False
    
    async def test_multi_crop_suitability(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test multi-crop suitability analysis."""
        result = await self.run_test_case(
            client,
            "Check current conditions in Des Moines, Iowa for corn, soybeans, and wheat - which crop has the best growing conditions right now?",
            "Multi-Crop Suitability Analysis",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            # Should use agricultural conditions multiple times for different crops
            agricultural_count = tools.count("get_agricultural_conditions")
            forecast_count = tools.count("get_weather_forecast")
            total_tools = len([t for t in tools if t != "finish"])
            
            print(f"📊 Tools summary: {agricultural_count} agricultural conditions, {forecast_count} weather forecasts")
            print(f"🔄 Total iterations: {result.get('iterations', 'unknown')}")
            
            # Verify we got at least 3 agricultural calls (one per crop)
            if agricultural_count >= 3:
                print(f"✅ Agricultural conditions tool used {agricultural_count} times")
                print(f"✅ Total of {total_tools} tool calls made")
                
                # Check if all three crops were analyzed
                corn_checked = False
                soy_checked = False
                wheat_checked = False
                
                for tool in result["tools_used"]:
                    if tool["name"] == "get_agricultural_conditions":
                        args = tool["args"]
                        crop_type = args.get('crop_type', '').lower()
                        if "corn" in crop_type:
                            corn_checked = True
                            print(f"✅ Corn conditions checked")
                        elif "soy" in crop_type:
                            soy_checked = True
                            print(f"✅ Soybean conditions checked")
                        elif "wheat" in crop_type:
                            wheat_checked = True
                            print(f"✅ Wheat conditions checked")
                
                if corn_checked and soy_checked and wheat_checked:
                    print("✅ All three crops analyzed successfully")
                    return True
                else:
                    if not corn_checked:
                        print("❌ Corn conditions not checked")
                    if not soy_checked:
                        print("❌ Soybean conditions not checked")
                    if not wheat_checked:
                        print("❌ Wheat conditions not checked")
                    return False
            else:
                print(f"❌ Expected at least 3 agricultural calls")
                print(f"   Got: {agricultural_count} agricultural calls")
                print(f"   All tools used: {tools}")
                return False
        return False
    
    async def test_historical_weather(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test historical weather data query."""
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        month_and_week_ago = (datetime.now() - timedelta(days=37)).strftime("%Y-%m-%d")
        
        result = await self.run_test_case(
            client,
            f"What was the weather like in San Francisco from {month_and_week_ago} to {month_ago}?",
            "Historical Weather Data",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            if "get_historical_weather" in tools:
                print("✅ Historical weather tool used correctly")
                # Check date parameters
                for tool in result["tools_used"]:
                    if tool["name"] == "get_historical_weather":
                        args = tool["args"]
                        if "start_date" in args and "end_date" in args:
                            print(f"✅ Date range passed: {args['start_date']} to {args['end_date']}")
                return True
            else:
                print(f"❌ Expected get_historical_weather but got: {tools}")
                return False
        return False
    
    async def test_multi_city_comparison(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test multi-city weather comparison."""
        result = await self.run_test_case(
            client,
            "Compare the weather in New York and Los Angeles",
            "Multi-City Weather Comparison",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            # Should use weather forecast tool, possibly multiple times
            if "get_weather_forecast" in tools:
                print("✅ Weather forecast tool used for comparison")
                # Count how many times the tool was used
                forecast_count = tools.count("get_weather_forecast")
                if forecast_count >= 2:
                    print(f"✅ Multiple forecast calls made ({forecast_count} times)")
                return True
            else:
                print(f"❌ Expected get_weather_forecast but got: {tools}")
                return False
        return False
    
    async def test_historical_current_comparison(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test comparison of historical and current weather."""
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        result = await self.run_test_case(
            client,
            f"Compare the historical weather from {month_ago} with the current forecast for Miami",
            "Historical vs Current Weather Comparison",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            # Should use both historical and forecast tools
            has_historical = "get_historical_weather" in tools
            has_forecast = "get_weather_forecast" in tools
            
            if has_historical and has_forecast:
                print("✅ Both historical and forecast tools used")
                return True
            else:
                print(f"❌ Expected both tools but got: {tools}")
                if not has_historical:
                    print("   Missing: get_historical_weather")
                if not has_forecast:
                    print("   Missing: get_weather_forecast")
                return False
        return False
    
    async def test_historical_multi_period_analysis(self, client: DurableAgentAPIClient, test_num: int = None, total: int = None) -> bool:
        """Test historical weather analysis for multiple time periods."""
        # Get last year's dates
        last_year = datetime.now().year - 1
        
        result = await self.run_test_case(
            client,
            f"Compare weather patterns in Napa Valley for the first week of February, March, and April {last_year}. Which month had the best conditions for vineyard work?",
            "Historical Multi-Period Weather Analysis",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            # Should use historical weather multiple times
            historical_count = tools.count("get_historical_weather")
            total_tools = len([t for t in tools if t != "finish"])
            
            print(f"📊 Tools summary: {historical_count} historical weather calls")
            print(f"🔄 Total iterations: {result.get('iterations', 'unknown')}")
            
            # Verify we got at least 3 historical calls (one per month)
            if historical_count >= 3:
                print(f"✅ Historical weather tool used {historical_count} times")
                print(f"✅ Total of {total_tools} tool calls made")
                
                # Check if all three months were analyzed
                feb_checked = False
                mar_checked = False
                apr_checked = False
                
                for tool in result["tools_used"]:
                    if tool["name"] == "get_historical_weather":
                        args = tool["args"]
                        dates = f"{args.get('start_date', '')} to {args.get('end_date', '')}"
                        if f"{last_year}-02" in dates:
                            feb_checked = True
                            print(f"✅ February {last_year} weather data fetched: {dates}")
                        elif f"{last_year}-03" in dates:
                            mar_checked = True
                            print(f"✅ March {last_year} weather data fetched: {dates}")
                        elif f"{last_year}-04" in dates:
                            apr_checked = True
                            print(f"✅ April {last_year} weather data fetched: {dates}")
                
                if feb_checked and mar_checked and apr_checked:
                    print("✅ All three months analyzed successfully")
                    return True
                else:
                    if not feb_checked:
                        print(f"❌ February {last_year} weather data not fetched")
                    if not mar_checked:
                        print(f"❌ March {last_year} weather data not fetched")
                    if not apr_checked:
                        print(f"❌ April {last_year} weather data not fetched")
                    return False
            else:
                print(f"❌ Expected at least 3 historical weather calls")
                print(f"   Got: {historical_count} historical calls")
                print(f"   All tools used: {tools}")
                return False
        return False
    
    async def run_all_tests(self, client: DurableAgentAPIClient, test_limit: Optional[int] = None) -> int:
        """Run agriculture tool integration tests."""
        all_tests = [
            ("Multi-Location Grape Growing Comparison", self.test_multi_location_comparison),
            ("Basic Weather Forecast", self.test_weather_forecast_basic),
            ("Weather with Recommendation", self.test_weather_forecast_with_recommendation),
            ("10-Day Forecast", self.test_10_day_forecast),
            ("Multi-Timeframe Weather Forecast", self.test_multi_timeframe_forecast),
            ("Agricultural Conditions", self.test_agricultural_conditions_basic),
            ("Agricultural with Crop", self.test_agricultural_with_crop),
            ("Tree Farm Conditions", self.test_tree_farm_conditions),
            ("Multi-Crop Suitability Analysis", self.test_multi_crop_suitability),
            ("Historical Weather", self.test_historical_weather),
            ("Multi-City Comparison", self.test_multi_city_comparison),
            ("Historical vs Current", self.test_historical_current_comparison),
            ("Historical Multi-Period Analysis", self.test_historical_multi_period_analysis),
        ]
        
        # Apply test limit if specified
        if test_limit is not None:
            tests = all_tests[:test_limit]
            if test_limit > len(all_tests):
                print(f"\n⚠️  Warning: Requested {test_limit} tests but only {len(all_tests)} available")
        else:
            tests = all_tests
        
        passed = 0
        failed = 0
        
        print("\n" + "=" * 80)
        if self.detailed:
            print("🌾 AGRICULTURE TOOL INTEGRATION TESTS - DETAILED REACT LOOP ANALYSIS")
        else:
            print("🌾 RUNNING AGRICULTURE TOOL INTEGRATION TESTS")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Running: {len(tests)} of {len(all_tests)} tests")
        if test_limit is not None:
            print(f"🎯 Test Limit: {test_limit}")
        if self.detailed:
            print(f"🔍 Mode: Detailed React Loop Visibility")
        print("=" * 80)
        
        test_results = []
        
        for i, (test_name, test_func) in enumerate(tests, 1):
            try:
                start_time = time.time()
                # Pass test number and total for detailed mode
                if self.detailed:
                    # Modify test functions to accept additional parameters
                    result = await test_func(client, i, len(tests))
                else:
                    result = await test_func(client)
                elapsed = time.time() - start_time
                
                if result:
                    passed += 1
                    status = "✅ PASSED"
                else:
                    failed += 1
                    status = "❌ FAILED"
                
                test_results.append({
                    "name": test_name,
                    "status": status,
                    "time": elapsed
                })
                
                if not self.detailed:
                    print(f"\n{status} - Test {i}/{len(tests)}: {test_name}")
                    print("-" * 80)
                
            except Exception as e:
                print(f"\n❌ CRASHED - Test {i}/{len(tests)}: {test_name}")
                print(f"Error: {e}")
                if not self.detailed:
                    print("-" * 80)
                failed += 1
                test_results.append({
                    "name": test_name,
                    "status": "❌ CRASHED",
                    "time": 0
                })
        
        # Final summary
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        if self.detailed:
            # Individual test results
            print("\n📋 Test Results:")
            for i, result in enumerate(test_results, 1):
                print(f"   {i}. {result['name']}")
                print(f"      Status: {result['status']}")
                print(f"      Time: {result['time']:.2f}s")
        
        # Overall statistics
        if self.detailed:
            print(f"\n📈 Overall Statistics:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success Rate: {(passed / len(tests) * 100):.1f}%")
        if self.detailed:
            print(f"   ⏱️  Total Time: {sum(r['time'] for r in test_results):.2f}s")
        print("=" * 80)
        
        return failed


async def main():
    """Run the agriculture integration tests."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run agriculture integration tests",
        epilog="Examples:\n"
               "  poetry run python integration_tests/test_agriculture.py          # Run all tests\n"
               "  poetry run python integration_tests/test_agriculture.py 2        # Run first 2 tests\n"
               "  poetry run python integration_tests/test_agriculture.py -d       # Run with detailed output\n"
               "  poetry run python integration_tests/test_agriculture.py -d 2     # Run first 2 tests with detailed output",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-d", "--detailed",
        action="store_true",
        help="Show detailed React loop analysis"
    )
    parser.add_argument(
        "num_tests",
        type=int,
        nargs="?",
        default=None,
        help="Number of tests to run (default: all tests)"
    )
    
    args = parser.parse_args()
    
    # Validate argument
    if args.num_tests is not None and args.num_tests < 1:
        print("❌ Error: Number of tests must be at least 1")
        sys.exit(1)
    
    if args.detailed:
        print("\n🚀 Starting Detailed Agriculture Integration Tests")
        print("   This test suite provides full visibility into the AI agent's React loop")
        print("   including reasoning, tool selection, and response synthesis.")
    
    client = DurableAgentAPIClient()
    test_suite = AgricultureIntegrationTest(detailed=args.detailed)
    
    # Check API health
    print("\n🏥 Checking API health...")
    if not await client.health_check():
        print("❌ API is not healthy. Make sure services are running with:")
        print("   docker-compose up")
        sys.exit(1)
    print("✅ API is healthy")
    
    # Run tests with specified limit
    failed = await test_suite.run_all_tests(client, test_limit=args.num_tests)
    
    # Exit with appropriate code
    sys.exit(failed)


if __name__ == "__main__":
    asyncio.run(main())