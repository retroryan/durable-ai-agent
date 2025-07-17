#!/usr/bin/env python3
"""
Integration test for the chat API endpoint with all AgricultureToolSet test cases.
Run with: poetry run python integration_tests/test_weather_api.py
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime

from utils.api_client import DurableAgentAPIClient
from shared.tool_utils.agriculture_tool_set import AgricultureToolSet


async def main():
    """Main test function."""
    print("🚀 Starting Weather API Integration Test")
    print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Get all test cases from AgricultureToolSet
    test_cases = AgricultureToolSet.get_test_cases()
    
    print(f"\n📊 Running {len(test_cases)} test cases from AgricultureToolSet")
    print("=" * 60)
    
    successful_tests = 0
    failed_tests = 0
    
    # Create API client
    # Use a longer timeout for complex queries
    async with DurableAgentAPIClient(timeout=60) as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📍 Test {i}/{len(test_cases)}: {test_case.description}")
            print(f"🎯 Scenario: {test_case.scenario}")
            print(f"🔧 Expected tools: {', '.join(test_case.expected_tools) if test_case.expected_tools else 'Multiple tools'}")
            print("-" * 40)
            
            user_name = f"test_user_{uuid.uuid4().hex[:8]}"
            # Prepend "weather:" to all queries to trigger the weather workflow
            weather_request = f"weather: {test_case.request}"
            print(f"Sending: '{weather_request}' from user: {user_name}")

            try:
                response = await client.chat(weather_request, user_name=user_name)
                print("\nResponse:")
                print(json.dumps(response, indent=2))

                print(f"\n✅ Success! Workflow ID: {response.get('workflow_id', 'N/A')}")
                successful_tests += 1
                
                # Check if it mentions specific scenarios
                last_response = response.get("last_response", {})
                response_message = ""
                if isinstance(last_response, dict):
                    response_message = last_response.get("message", "").lower()
                elif isinstance(last_response, str):
                    response_message = last_response.lower()
                
                if test_case.scenario == "forecast" and "forecast" in response_message:
                    print("🌤️  Weather forecast information detected!")
                elif test_case.scenario == "agriculture" and any(word in response_message for word in ["soil", "crop", "plant", "agricult"]):
                    print("🌱 Agricultural information detected!")
                elif test_case.scenario == "historical" and "historical" in response_message:
                    print("📊 Historical weather data detected!")
                elif test_case.scenario == "comparison" and any(word in response_message for word in ["compar", "both", "versus"]):
                    print("⚖️  Comparison detected!")
            except Exception as e:
                print(f"\n❌ Failed to get response: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                failed_tests += 1

            # Wait a bit between calls to avoid overwhelming the API
            await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print(f"✨ Test completed! Results:")
    print(f"   ✅ Successful: {successful_tests}/{len(test_cases)}")
    print(f"   ❌ Failed: {failed_tests}/{len(test_cases)}")
    
    if failed_tests == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed")
        return 1


def check_services():
    """Check if required services are running."""
    import httpx
    
    print("🔍 Checking services...")

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
        print("\n💡 Make sure to run: docker-compose up")
        return False

    return True


if __name__ == "__main__":
    print("🏗️  Durable AI Agent - Chat API Test")
    print("=" * 60)

    # Check if services are running
    if not check_services():
        print("\n⚠️  Please start the services before running this test.")
        print("   Run: docker-compose up")
        sys.exit(1)

    print("")

    # Run the async main function
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        sys.exit(1)