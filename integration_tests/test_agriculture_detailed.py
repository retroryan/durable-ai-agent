#!/usr/bin/env python3
"""
Detailed Integration Tests for Agriculture Tool Use Cases with React Loop Visibility

This test suite provides comprehensive visibility into the AI agent's reasoning process
by displaying the complete React (Reason-Act) loop execution similar to demo_react_agent.py.

The tests demonstrate:
1. How the agent reasons about user queries (Thought)
2. Which tools it selects and why (Action)
3. What results it obtains (Observation)
4. How it synthesizes the final answer (Extract)

Each test case shows:
- Query processing and workflow initialization
- React agent execution with timing and iterations
- Tool execution details with arguments
- Extract agent synthesis
- Full untruncated responses

This provides transparency into the AI's decision-making process and helps debug
tool selection, argument passing, and response generation.

Usage:
    poetry run python integration_tests/test_agriculture_detailed.py        # Run all tests
    poetry run python integration_tests/test_agriculture_detailed.py 2      # Run first 2 tests
    poetry run python integration_tests/test_agriculture_detailed.py 1      # Run only first test
"""
import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import time

from utils.api_client import DurableAgentAPIClient


class DetailedAgricultureIntegrationTest:
    """
    Integration tests for agriculture tools with detailed React loop visibility.
    
    This test class provides comprehensive insights into the AI agent's reasoning
    process by capturing and displaying:
    - Workflow execution details
    - React loop iterations
    - Tool selection reasoning
    - Execution timing
    - Final answer synthesis
    """
    
    async def query_workflow_details(self, client: DurableAgentAPIClient, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Query workflow for comprehensive execution details.
        
        This method retrieves detailed information about the workflow execution including:
        - Current status and iteration count
        - Tools used during execution
        - Execution timing
        - Message counts
        
        Args:
            client: API client instance
            workflow_id: The workflow ID to query
            
        Returns:
            Dictionary with workflow details or None if not found
        """
        try:
            # First try the standard query endpoint
            response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/query"
            )
            if response.status_code == 200:
                return response.json()
            
            # If that doesn't work, try workflow status
            status_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/workflow-status"
            )
            if status_response.status_code == 200:
                return status_response.json()
                
            return None
        except Exception as e:
            print(f"⚠️  Could not query workflow details: {e}")
            return None
    
    async def wait_for_agent_response_with_progress(self, client: DurableAgentAPIClient, workflow_id: str, timeout: int = 60) -> Tuple[bool, float]:
        """
        Wait for agent response while showing progress indicators.
        
        This method now uses the /status endpoint like the frontend does,
        to test the exact same code path including message serialization.
        
        Args:
            client: API client instance
            workflow_id: The workflow ID to monitor
            timeout: Maximum time to wait in seconds
            
        Returns:
            Tuple of (success: bool, elapsed_time: float)
        """
        start_time = time.time()
        max_attempts = timeout // 2
        
        print("⏳ Waiting for agent response", end="", flush=True)
        
        for attempt in range(max_attempts):
            await asyncio.sleep(2)  # Poll every 2 seconds
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
                        print(f"\n✅ Got agent response after {elapsed:.2f} seconds")
                        # Log what we received for debugging
                        print(f"   Status: {status_data.get('status')}")
                        print(f"   Messages in history: {len(conversation_history)}")
                        return True, elapsed
            
            # Also check last_response for compatibility
            last_response = status_data.get("last_response", {})
            if last_response and last_response.get("message") != "Processing your request...":
                elapsed = time.time() - start_time
                print(f"\n✅ Got agent response after {elapsed:.2f} seconds")
                return True, elapsed
        
        elapsed = time.time() - start_time
        print(f"\n❌ No agent response after {timeout} seconds")
        return False, elapsed
    
    def format_trajectory_step(self, trajectory: Dict[str, Any], index: int) -> str:
        """
        Format a single trajectory step for display.
        
        This method creates a visually appealing representation of a single
        React loop iteration, showing the thought process, tool selection,
        and observations.
        
        Args:
            trajectory: Single trajectory dictionary
            index: Step number (1-based)
            
        Returns:
            Formatted string representation of the trajectory step
        """
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
            # Truncate very long observations but show more than before
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
    
    async def run_detailed_test_case(self, client: DurableAgentAPIClient, query: str, test_name: str, test_number: int, total_tests: int) -> Dict[str, Any]:
        """
        Run a single test case with detailed React loop visibility.
        
        This is the core test execution method that:
        1. Starts a workflow with the user query
        2. Monitors execution progress
        3. Retrieves and displays React loop details
        4. Shows tool execution and final synthesis
        5. Validates expected outcomes
        
        Args:
            client: API client instance
            query: User query to test
            test_name: Descriptive name of the test
            test_number: Current test number
            total_tests: Total number of tests
            
        Returns:
            Dictionary containing test results and execution details
        """
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        
        # Test header with clear visual separation
        print(f"\n{'='*80}")
        print(f"{'🧪 Test Case ' + str(test_number) + '/' + str(total_tests):^80}")
        print(f"{'='*80}")
        print(f"📋 Test Name: {test_name}")
        print(f"📤 Query: {query}")
        print(f"👤 User: {user_name}")
        print(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("─" * 80)
        
        try:
            # Start workflow
            print("\n▶️  Starting workflow...")
            start_time = time.time()
            initial_response = await client.chat(query, user_name=user_name)
            workflow_id = initial_response.get("workflow_id")
            
            if not workflow_id:
                print("❌ No workflow_id in response")
                return {"success": False, "error": "No workflow_id"}
            
            print(f"✅ Workflow started: {workflow_id}")
            
            # Wait for agent response with progress
            print("\n" + "─" * 60)
            print("🔄 React Agent Execution")
            print("─" * 60)
            
            success, response_time = await self.wait_for_agent_response_with_progress(client, workflow_id)
            if not success:
                return {"success": False, "error": "No agent response"}
            
            # Query workflow details
            workflow_details = await self.query_workflow_details(client, workflow_id)
            if workflow_details:
                print(f"\n📊 Workflow Details:")
                print(f"   - Status: {workflow_details.get('status', 'unknown')}")
                print(f"   - Message Count: {workflow_details.get('message_count', 0)}")
                print(f"   - Interaction Count: {workflow_details.get('interaction_count', 0)}")
            
            # Get trajectories
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
            
            # Display trajectory summary
            if summary:
                print(f"\n📈 Summary: {summary}")
            
            # Display each trajectory step
            tools_used = []
            for i, traj in enumerate(trajectories, 1):
                if isinstance(traj, dict):
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
                    print(self.format_trajectory_step(traj_dict, i))
                    if traj.tool_name:
                        tools_used.append({
                            "name": traj.tool_name,
                            "args": traj.tool_args
                        })
            
            # Get final response (use status endpoint to match frontend)
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
            
            print("✅ Answer extracted successfully")
            
            # Display results
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
            
            return {
                "success": True,
                "tools_used": tools_used,
                "final_message": final_message,
                "workflow_id": workflow_id,
                "execution_time": total_time,
                "iterations": len(trajectories),
                "trajectories": trajectories
            }
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def test_weather_forecast_with_details(self, client: DurableAgentAPIClient, test_num: int, total: int) -> bool:
        """Test weather forecast with full React loop visibility."""
        result = await self.run_detailed_test_case(
            client,
            "What's the weather like in New York and should I bring an umbrella?",
            "Weather Forecast with Umbrella Recommendation",
            test_num,
            total
        )
        
        if result["success"]:
            # Validate results
            tools = [t["name"] for t in result["tools_used"]]
            if "get_weather_forecast" in tools:
                print("\n✅ Test Passed: Weather forecast tool used correctly")
                return True
            else:
                print(f"\n❌ Test Failed: Expected get_weather_forecast but got: {tools}")
                return False
        return False
    
    async def test_agricultural_conditions_with_details(self, client: DurableAgentAPIClient, test_num: int, total: int) -> bool:
        """Test agricultural conditions with full React loop visibility."""
        result = await self.run_detailed_test_case(
            client,
            "Are conditions good for planting corn in Ames, Iowa?",
            "Agricultural Conditions for Corn Planting",
            test_num,
            total
        )
        
        if result["success"]:
            tools_used = result["tools_used"]
            if tools_used and tools_used[0]["name"] == "get_agricultural_conditions":
                print("\n✅ Test Passed: Agricultural conditions tool used")
                # Check if crop_type was passed
                args = tools_used[0]["args"]
                if "crop_type" in args and "corn" in str(args["crop_type"]).lower():
                    print("✅ Crop type (corn) passed correctly")
                return True
            else:
                print(f"\n❌ Test Failed: Expected get_agricultural_conditions")
                return False
        return False
    
    async def test_historical_weather_with_details(self, client: DurableAgentAPIClient, test_num: int, total: int) -> bool:
        """Test historical weather with full React loop visibility."""
        month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        month_and_week_ago = (datetime.now() - timedelta(days=37)).strftime("%Y-%m-%d")
        
        result = await self.run_detailed_test_case(
            client,
            f"What was the weather like in San Francisco from {month_and_week_ago} to {month_ago}?",
            "Historical Weather Data Query",
            test_num,
            total
        )
        
        if result["success"]:
            tools = [t["name"] for t in result["tools_used"]]
            if "get_historical_weather" in tools:
                print("\n✅ Test Passed: Historical weather tool used correctly")
                return True
            else:
                print(f"\n❌ Test Failed: Expected get_historical_weather but got: {tools}")
                return False
        return False
    
    async def test_multi_location_comparison_with_details(self, client: DurableAgentAPIClient, test_num: int, total: int) -> bool:
        """Test multi-location weather comparison with full React loop visibility."""
        result = await self.run_detailed_test_case(
            client,
            "Compare the weather in New York and Los Angeles",
            "Multi-City Weather Comparison",
            test_num,
            total
        )
        
        if result["success"]:
            # Should use weather forecast tool multiple times
            tools = [t["name"] for t in result["tools_used"]]
            forecast_count = tools.count("get_weather_forecast")
            if forecast_count >= 2:
                print(f"\n✅ Test Passed: Multiple forecast calls made ({forecast_count} times)")
                return True
            else:
                print(f"\n❌ Test Failed: Expected multiple forecast calls but got {forecast_count}")
                return False
        return False
    
    async def run_all_detailed_tests(self, client: DurableAgentAPIClient, test_limit: Optional[int] = None) -> int:
        """
        Run agriculture tool integration tests with detailed output.
        
        This method orchestrates the execution of test cases, providing:
        - Clear visual separation between tests
        - Comprehensive execution details
        - Summary statistics
        - Success/failure tracking
        
        Args:
            client: API client instance
            test_limit: Maximum number of tests to run (None for all tests)
        
        Returns:
            Number of failed tests
        """
        all_tests = [
            ("Weather Forecast with Recommendation", self.test_weather_forecast_with_details),
            ("Agricultural Conditions for Planting", self.test_agricultural_conditions_with_details),
            ("Historical Weather Query", self.test_historical_weather_with_details),
            ("Multi-Location Comparison", self.test_multi_location_comparison_with_details),
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
        print("🌾 AGRICULTURE TOOL INTEGRATION TESTS - DETAILED REACT LOOP ANALYSIS")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Running: {len(tests)} of {len(all_tests)} tests")
        if test_limit is not None:
            print(f"🎯 Test Limit: {test_limit}")
        print(f"🔍 Mode: Detailed React Loop Visibility")
        print("=" * 80)
        
        test_results = []
        
        for i, (test_name, test_func) in enumerate(tests, 1):
            try:
                start_time = time.time()
                result = await test_func(client, i, len(tests))
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
                
            except Exception as e:
                print(f"\n❌ CRASHED - Test {i}/{len(tests)}: {test_name}")
                print(f"Error: {e}")
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
        
        # Individual test results
        print("\n📋 Test Results:")
        for i, result in enumerate(test_results, 1):
            print(f"   {i}. {result['name']}")
            print(f"      Status: {result['status']}")
            print(f"      Time: {result['time']:.2f}s")
        
        # Overall statistics
        print(f"\n📈 Overall Statistics:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success Rate: {(passed / len(tests) * 100):.1f}%")
        print(f"   ⏱️  Total Time: {sum(r['time'] for r in test_results):.2f}s")
        print("=" * 80)
        
        return failed


async def main():
    """
    Main entry point for the detailed agriculture integration tests.
    
    This function:
    1. Parses command-line arguments
    2. Initializes the API client
    3. Checks API health
    4. Runs specified number of tests
    5. Reports results and exits with appropriate code
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run detailed agriculture integration tests with React loop visibility",
        epilog="Examples:\n"
               "  poetry run python integration_tests/test_agriculture_detailed.py        # Run all tests\n"
               "  poetry run python integration_tests/test_agriculture_detailed.py 2      # Run first 2 tests\n"
               "  poetry run python integration_tests/test_agriculture_detailed.py 1      # Run only first test",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
    
    print("\n🚀 Starting Detailed Agriculture Integration Tests")
    print("   This test suite provides full visibility into the AI agent's React loop")
    print("   including reasoning, tool selection, and response synthesis.")
    
    client = DurableAgentAPIClient()
    test_suite = DetailedAgricultureIntegrationTest()
    
    # Check API health
    print("\n🏥 Checking API health...")
    if not await client.health_check():
        print("❌ API is not healthy. Make sure services are running with:")
        print("   docker-compose up")
        sys.exit(1)
    print("✅ API is healthy")
    
    # Run tests with specified limit
    failed = await test_suite.run_all_detailed_tests(client, test_limit=args.num_tests)
    
    # Exit with appropriate code
    sys.exit(failed)


if __name__ == "__main__":
    asyncio.run(main())