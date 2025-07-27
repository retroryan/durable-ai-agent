#!/usr/bin/env python3
"""
Integration tests for agriculture tool use cases.
Run with: poetry run python integration_tests/test_agriculture.py

This test verifies all agriculture tool use cases by sending queries to the API server.
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from utils.api_client import DurableAgentAPIClient


class AgricultureIntegrationTest:
    """Integration tests for agriculture tool use cases."""
    
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
                print(f"✅ Got agent response after {(attempt + 1) * 2} seconds")
                return True
        
        print(f"❌ No agent response after {timeout} seconds")
        return False
    
    async def run_test_case(self, client: DurableAgentAPIClient, query: str, test_name: str) -> Dict[str, Any]:
        """Run a single test case and return results."""
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        
        print(f"\n{'='*80}")
        print(f"🧪 TEST: {test_name}")
        print(f"{'='*80}")
        print(f"📤 Query: {query}")
        print("-" * 80)
        
        try:
            # Send request to start workflow
            initial_response = await client.chat(query, user_name=user_name)
            workflow_id = initial_response.get("workflow_id")
            
            if not workflow_id:
                print("❌ No workflow_id in response")
                return {"success": False, "error": "No workflow_id"}
            
            print(f"✅ Workflow started: {workflow_id}")
            
            # Poll for agent response
            print("⏳ Polling for agent response...")
            if not await self.wait_for_agent_response(client, workflow_id):
                return {"success": False, "error": "No agent response"}
            
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
            final_message = messages[-1].get("content", "") if messages else ""
            
            # Extract tools used
            tools_used = []
            for traj in trajectories:
                if isinstance(traj, dict):
                    tool_name = traj.get("tool_name", "")
                    tool_args = traj.get("tool_args", {})
                else:
                    tool_name = traj.tool_name
                    tool_args = traj.tool_args
                
                if tool_name:
                    tools_used.append({
                        "name": tool_name,
                        "args": tool_args
                    })
            
            # Print tools used summary
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
                "workflow_id": workflow_id
            }
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def test_weather_forecast_basic(self, client: DurableAgentAPIClient) -> bool:
        """Test basic weather forecast request."""
        result = await self.run_test_case(
            client,
            "What's the weather forecast for New York City?",
            "Basic Weather Forecast"
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
    
    async def test_weather_forecast_with_recommendation(self, client: DurableAgentAPIClient) -> bool:
        """Test weather forecast with umbrella recommendation."""
        result = await self.run_test_case(
            client,
            "What's the weather like in New York and should I bring an umbrella?",
            "Weather Forecast with Recommendation"
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
    
    async def test_10_day_forecast(self, client: DurableAgentAPIClient) -> bool:
        """Test 10-day weather forecast."""
        result = await self.run_test_case(
            client,
            "I need the 10-day weather forecast for London",
            "10-Day Weather Forecast"
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
    
    async def test_agricultural_conditions_basic(self, client: DurableAgentAPIClient) -> bool:
        """Test agricultural conditions request."""
        result = await self.run_test_case(
            client,
            "What are the agricultural conditions in Des Moines, Iowa?",
            "Agricultural Conditions"
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
    
    async def test_agricultural_with_crop(self, client: DurableAgentAPIClient) -> bool:
        """Test agricultural conditions with specific crop."""
        result = await self.run_test_case(
            client,
            "Are conditions good for planting corn in Ames, Iowa?",
            "Agricultural Conditions for Corn"
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
    
    async def test_tree_farm_conditions(self, client: DurableAgentAPIClient) -> bool:
        """Test agricultural conditions for tree farm."""
        result = await self.run_test_case(
            client,
            "What are the soil moisture levels at my tree farm in Olympia, Washington?",
            "Tree Farm Conditions"
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
    
    async def test_historical_weather(self, client: DurableAgentAPIClient) -> bool:
        """Test historical weather data query."""
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        month_and_week_ago = (datetime.now() - timedelta(days=37)).strftime("%Y-%m-%d")
        
        result = await self.run_test_case(
            client,
            f"What was the weather like in San Francisco from {month_and_week_ago} to {month_ago}?",
            "Historical Weather Data"
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
    
    async def test_multi_city_comparison(self, client: DurableAgentAPIClient) -> bool:
        """Test multi-city weather comparison."""
        result = await self.run_test_case(
            client,
            "Compare the weather in New York and Los Angeles",
            "Multi-City Weather Comparison"
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
    
    async def test_historical_current_comparison(self, client: DurableAgentAPIClient) -> bool:
        """Test comparison of historical and current weather."""
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        result = await self.run_test_case(
            client,
            f"Compare the historical weather from {month_ago} with the current forecast for Miami",
            "Historical vs Current Weather Comparison"
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
    
    async def run_all_tests(self, client: DurableAgentAPIClient) -> int:
        """Run all agriculture tool integration tests."""
        tests = [
            ("Basic Weather Forecast", self.test_weather_forecast_basic),
            ("Weather with Recommendation", self.test_weather_forecast_with_recommendation),
            ("10-Day Forecast", self.test_10_day_forecast),
            ("Agricultural Conditions", self.test_agricultural_conditions_basic),
            ("Agricultural with Crop", self.test_agricultural_with_crop),
            ("Tree Farm Conditions", self.test_tree_farm_conditions),
            ("Historical Weather", self.test_historical_weather),
            ("Multi-City Comparison", self.test_multi_city_comparison),
            ("Historical vs Current", self.test_historical_current_comparison),
        ]
        
        passed = 0
        failed = 0
        
        print("\n" + "=" * 80)
        print("🌾 RUNNING AGRICULTURE TOOL INTEGRATION TESTS")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Total Tests: {len(tests)}")
        print("=" * 80)
        
        for i, (test_name, test_func) in enumerate(tests, 1):
            try:
                result = await test_func(client)
                if result:
                    passed += 1
                    status = "✅ PASSED"
                else:
                    failed += 1
                    status = "❌ FAILED"
                print(f"\n{status} - Test {i}/{len(tests)}: {test_name}")
                print("-" * 80)
            except Exception as e:
                print(f"\n❌ CRASHED - Test {i}/{len(tests)}: {test_name}")
                print(f"Error: {e}")
                print("-" * 80)
                failed += 1
        
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed / len(tests) * 100):.1f}%")
        print("=" * 80)
        
        return failed


async def main():
    """Run the agriculture integration tests."""
    client = DurableAgentAPIClient()
    test_suite = AgricultureIntegrationTest()
    
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