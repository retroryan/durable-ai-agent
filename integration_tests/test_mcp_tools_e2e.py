#!/usr/bin/env python3
"""
End-to-end integration test for MCP tools with mock mode.
Run with: poetry run python integration_tests/test_mcp_tools_e2e.py

IMPORTANT: This test requires services to be running with TOOLS_MOCK=true
Run: TOOLS_MOCK=true docker-compose --profile weather_proxy up -d
"""
import asyncio
import json
import sys
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List

from utils.api_client import DurableAgentAPIClient


class MCPToolsE2ETest:
    """End-to-end test for MCP tools integration."""
    
    def __init__(self):
        self.test_cases = self._get_test_cases()
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def _get_test_cases(self) -> List[Dict[str, Any]]:
        """Get test cases specifically for MCP tools."""
        return [
            {
                "name": "MCP Weather Forecast",
                "description": "Test MCP weather forecast tool",
                "request": "weather: Get the weather forecast for Portland using the MCP forecast service",
                "expected_tool": "get_weather_forecast_mcp",
                "expected_content": ["forecast", "temperature", "precipitation"],
            },
            {
                "name": "MCP Historical Weather",
                "description": "Test MCP historical weather tool",
                "request": "weather: Get historical weather data for Chicago from last week using the MCP historical service",
                "expected_tool": "get_historical_weather_mcp",
                "expected_content": ["historical", "past", "temperature"],
            },
            {
                "name": "MCP Agricultural Conditions",
                "description": "Test MCP agricultural conditions tool",
                "request": "weather: Check agricultural conditions for corn farming in Iowa using the MCP agricultural service",
                "expected_tool": "get_agricultural_conditions_mcp",
                "expected_content": ["agricultural", "soil", "moisture"],
            },
            {
                "name": "Multiple MCP Tools",
                "description": "Test multiple MCP tool calls in one query",
                "request": "weather: I'm planning to plant soybeans in Des Moines. Check current conditions and 7-day forecast using MCP services.",
                "expected_tools": ["get_weather_forecast_mcp", "get_agricultural_conditions_mcp"],
                "expected_content": ["forecast", "agricultural", "soybean"],
            },
            {
                "name": "MCP vs Traditional Comparison",
                "description": "Test using both MCP and traditional tools",
                "request": "weather: Compare the weather forecast from both traditional and MCP services for Denver",
                "expected_tools": ["get_weather_forecast", "get_weather_forecast_mcp"],
                "expected_content": ["forecast", "comparison", "denver"],
            },
        ]
    
    async def check_services(self) -> bool:
        """Check if required services are running."""
        import httpx
        
        print("🔍 Checking services...")
        
        # Check if TOOLS_MOCK is set
        if os.getenv("TOOLS_MOCK", "false").lower() != "true":
            print("⚠️  WARNING: TOOLS_MOCK is not set to true")
            print("   Set TOOLS_MOCK=true in your environment for predictable tests")
        
        try:
            # Check API
            response = httpx.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                print("✅ API server is running on port 8000")
            else:
                print("❌ API server returned non-200 status")
                return False
        except Exception as e:
            print("❌ API server is not accessible on port 8000")
            print(f"   Error: {e}")
            print("\n💡 Make sure to run: TOOLS_MOCK=true docker-compose --profile weather_proxy up")
            return False
        
        # Check MCP proxy
        try:
            response = httpx.get("http://localhost:8001/health", timeout=5.0)
            print("✅ MCP proxy is running on port 8001")
        except Exception:
            print("⚠️  MCP proxy not accessible on port 8001 (may be using individual services)")
        
        return True
    
    def _analyze_trajectory(self, response: Dict[str, Any], test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the trajectory to verify MCP tool usage."""
        analysis = {
            "success": False,
            "mcp_tools_used": [],
            "all_tools_used": [],
            "observations": []
        }
        
        try:
            # Extract trajectory from response
            last_response = response.get("last_response", {})
            if isinstance(last_response, dict):
                trajectory = last_response.get("trajectory", {})
            else:
                return analysis
            
            # Find all tool calls in trajectory
            for key, value in trajectory.items():
                if key.startswith("tool_name_"):
                    tool_name = value
                    analysis["all_tools_used"].append(tool_name)
                    if tool_name.endswith("_mcp"):
                        analysis["mcp_tools_used"].append(tool_name)
                elif key.startswith("observation_"):
                    analysis["observations"].append(value)
            
            # Check if expected tools were used
            if "expected_tool" in test_case:
                analysis["success"] = test_case["expected_tool"] in analysis["all_tools_used"]
            elif "expected_tools" in test_case:
                found_tools = set(analysis["all_tools_used"])
                expected_tools = set(test_case["expected_tools"])
                analysis["success"] = bool(found_tools & expected_tools)
            
            return analysis
            
        except Exception as e:
            print(f"   Error analyzing trajectory: {e}")
            return analysis
    
    def _check_mock_response(self, observations: List[str]) -> bool:
        """Check if responses contain mock data indicators."""
        mock_indicators = ['"mock": true', '"mock":true', 'Mock weather', 'Mock historical', 'Mock agricultural']
        
        for obs in observations:
            obs_str = str(obs).lower()
            if any(indicator.lower() in obs_str for indicator in mock_indicators):
                return True
        return False
    
    async def run_test_case(self, client: DurableAgentAPIClient, test_case: Dict[str, Any]) -> bool:
        """Run a single test case."""
        print(f"\n📍 Test: {test_case['name']}")
        print(f"📝 {test_case['description']}")
        print(f"🎯 Expected tool(s): {test_case.get('expected_tool') or ', '.join(test_case.get('expected_tools', []))}")
        print("-" * 60)
        
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        print(f"Sending: '{test_case['request']}' from user: {user_name}")
        
        try:
            response = await client.chat(test_case['request'], user_name=user_name)
            
            # Analyze trajectory
            analysis = self._analyze_trajectory(response, test_case)
            
            print(f"\n📊 Analysis:")
            print(f"   All tools used: {', '.join(analysis['all_tools_used']) or 'None'}")
            print(f"   MCP tools used: {', '.join(analysis['mcp_tools_used']) or 'None'}")
            
            # Check for mock data
            is_mock = self._check_mock_response(analysis['observations'])
            if is_mock:
                print("   ✅ Mock data detected (TOOLS_MOCK=true is working)")
            
            # Check content expectations
            last_response = response.get("last_response", {})
            response_message = ""
            if isinstance(last_response, dict):
                response_message = last_response.get("message", "").lower()
            elif isinstance(last_response, str):
                response_message = last_response.lower()
            
            content_found = []
            for expected in test_case.get("expected_content", []):
                if expected.lower() in response_message:
                    content_found.append(expected)
            
            if content_found:
                print(f"   ✅ Found expected content: {', '.join(content_found)}")
            
            # Determine success
            if analysis["success"]:
                print(f"\n✅ Test passed! Workflow ID: {response.get('workflow_id', 'N/A')}")
                self.results["passed"] += 1
                return True
            else:
                print(f"\n❌ Test failed: Expected tool(s) not found in trajectory")
                self.results["failed"] += 1
                self.results["errors"].append(f"{test_case['name']}: Expected tools not used")
                return False
                
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_case['name']}: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all test cases."""
        print("🚀 Starting MCP Tools E2E Integration Test")
        print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Check services first
        if not await self.check_services():
            print("\n⚠️  Please start the services before running this test.")
            print("   Run: TOOLS_MOCK=true docker-compose --profile weather_proxy up")
            return 1
        
        print(f"\n📊 Running {len(self.test_cases)} MCP tool test cases")
        print("=" * 80)
        
        # Create API client and run tests
        async with DurableAgentAPIClient() as client:
            for i, test_case in enumerate(self.test_cases, 1):
                print(f"\n🧪 Test {i}/{len(self.test_cases)}")
                await self.run_test_case(client, test_case)
                
                # Wait between tests
                if i < len(self.test_cases):
                    await asyncio.sleep(2)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 Test Summary:")
        print(f"   ✅ Passed: {self.results['passed']}/{len(self.test_cases)}")
        print(f"   ❌ Failed: {self.results['failed']}/{len(self.test_cases)}")
        
        if self.results["errors"]:
            print("\n❌ Errors:")
            for error in self.results["errors"]:
                print(f"   - {error}")
        
        if self.results["failed"] == 0:
            print("\n🎉 All MCP tool tests passed!")
            return 0
        else:
            print(f"\n⚠️  {self.results['failed']} test(s) failed")
            return 1


async def main():
    """Main entry point."""
    test = MCPToolsE2ETest()
    return await test.run_all_tests()


if __name__ == "__main__":
    print("🏗️  Durable AI Agent - MCP Tools E2E Test")
    print("=" * 80)
    
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