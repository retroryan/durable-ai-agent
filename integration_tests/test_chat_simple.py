#!/usr/bin/env python3
"""
Simple integration test for the chat API endpoint.
Run with: poetry run python integration_tests/test_chat_simple.py
"""
import asyncio
import json
import sys
from datetime import datetime

import httpx


async def call_chat_api(message: str, base_url: str = "http://localhost:8000") -> dict:
    """Call the chat API endpoint and return the response."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{base_url}/chat", json={"message": message})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {"error": str(e)}


async def main():
    """Main test function."""
    print("🚀 Starting Chat API Integration Test")
    print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Test 1: Weather message (should trigger child workflow)
    print("\n📍 Test 1: Weather Message")
    print("-" * 40)
    weather_message = "What's the weather forecast for tomorrow?"
    print(f"Sending: '{weather_message}'")

    response = await call_chat_api(weather_message)
    print("\nResponse:")
    print(json.dumps(response, indent=2))

    if "error" not in response:
        print(f"\n✅ Success! Workflow ID: {response.get('workflow_id', 'N/A')}")
    else:
        print("\n❌ Failed to get response")

    # Wait a bit between calls
    await asyncio.sleep(1)

    # Test 2: Non-weather message (regular workflow)
    print("\n\n📍 Test 2: Normal Message")
    print("-" * 40)
    normal_message = "Find me some interesting events in the city"
    print(f"Sending: '{normal_message}'")

    response = await call_chat_api(normal_message)
    print("\nResponse:")
    print(json.dumps(response, indent=2))

    if "error" not in response:
        print(f"\n✅ Success! Workflow ID: {response.get('workflow_id', 'N/A')}")
    else:
        print("\n❌ Failed to get response")

    # Wait a bit between calls
    await asyncio.sleep(1)

    # Test 3: The specific weather query from the child workflow
    print("\n\n📍 Test 3: Specific Weather Query")
    print("-" * 40)
    specific_message = "weather in San Francisco"
    print(f"Sending: '{specific_message}'")

    response = await call_chat_api(specific_message)
    print("\nResponse:")
    print(json.dumps(response, indent=2))

    if "error" not in response:
        print(f"\n✅ Success! Workflow ID: {response.get('workflow_id', 'N/A')}")
        # Check if it mentions child workflow
        if "child workflow" in response.get("message", "").lower():
            print("🎯 Child workflow was triggered!")
    else:
        print("\n❌ Failed to get response")

    print("\n" + "=" * 60)
    print("✨ Test completed!")


def check_services():
    """Check if required services are running."""
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
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        sys.exit(1)
