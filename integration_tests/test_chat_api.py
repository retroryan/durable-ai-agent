"""Integration test that calls the chat API endpoint and prints responses."""
import json

import pytest
from utils.api_client import DurableAgentAPIClient


@pytest.mark.api
class TestChatAPI:
    """Test chat API endpoint with detailed response printing."""

    @pytest.mark.asyncio
    async def test_chat_weather_message(self):
        """Test sending a weather message to the chat API and print the response."""
        async with DurableAgentAPIClient() as api_client:
            # Test weather message that should trigger the child workflow
            weather_message = "What's the weather like today?"

            print(f"\n=== Testing Chat API with Weather Message ===")
            print(f"Sending message: '{weather_message}'")

            try:
                response = await api_client.chat(weather_message)

                print(f"\n=== Chat API Response ===")
                print(json.dumps(response, indent=2))

                # Basic assertions
                assert "workflow_id" in response
                assert "message" in response
                assert "status" in response

                print(f"\n✅ Test passed! Workflow ID: {response['workflow_id']}")

            except Exception as e:
                print(f"\n❌ Test failed with error: {e}")
                raise

    @pytest.mark.asyncio
    async def test_chat_non_weather_message(self):
        """Test sending a non-weather message to the chat API and print the response."""
        async with DurableAgentAPIClient() as api_client:
            # Test non-weather message that should use normal workflow
            normal_message = "Find some events in the city"

            print(f"\n=== Testing Chat API with Normal Message ===")
            print(f"Sending message: '{normal_message}'")

            try:
                response = await api_client.chat(normal_message)

                print(f"\n=== Chat API Response ===")
                print(json.dumps(response, indent=2))

                # Basic assertions
                assert "workflow_id" in response
                assert "message" in response
                assert "status" in response

                print(f"\n✅ Test passed! Workflow ID: {response['workflow_id']}")

            except Exception as e:
                print(f"\n❌ Test failed with error: {e}")
                raise

    @pytest.mark.asyncio
    async def test_chat_multiple_messages(self):
        """Test sending multiple different messages and comparing responses."""
        async with DurableAgentAPIClient() as api_client:
            test_messages = [
                "What's the weather forecast?",
                "Find events near me",
                "Tell me about historical weather",
                "Show me agriculture information",
            ]

            print(f"\n=== Testing Multiple Chat Messages ===")

            for i, message in enumerate(test_messages, 1):
                print(f"\n--- Test {i}: '{message}' ---")

                try:
                    response = await api_client.chat(message)

                    print(f"Response summary:")
                    print(f"  Workflow ID: {response.get('workflow_id', 'N/A')}")
                    print(f"  Status: {response.get('status', 'N/A')}")
                    print(f"  Message: {response.get('message', 'N/A')[:100]}...")
                    print(f"  Query Count: {response.get('query_count', 'N/A')}")

                    # Basic assertions
                    assert "workflow_id" in response
                    assert "status" in response

                except Exception as e:
                    print(f"❌ Failed for message '{message}': {e}")
                    raise

            print(f"\n✅ All {len(test_messages)} messages tested successfully!")


if __name__ == "__main__":
    """Run the test directly for quick testing."""
    import asyncio

    async def run_direct_test():
        """Run a simple direct test without pytest."""
        print("🚀 Running direct chat API test...")

        async with DurableAgentAPIClient() as client:
            # Test weather message
            print("\n=== Direct Weather Test ===")
            response = await client.chat("What's the weather like?")
            print("Weather response:")
            print(json.dumps(response, indent=2))

            # Test normal message
            print("\n=== Direct Normal Test ===")
            response = await client.chat("Find me some events")
            print("Normal response:")
            print(json.dumps(response, indent=2))

    # Run if called directly
    asyncio.run(run_direct_test())
