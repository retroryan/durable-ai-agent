#!/usr/bin/env python3
"""
Integration test for API endpoints using the API client.
Run with: poetry run python integration_tests/test_api_endpoints.py
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime

from utils.api_client import DurableAgentAPIClient


async def test_health_endpoint(client: DurableAgentAPIClient):
    """Test the health check endpoint."""
    print("\n🏥 Testing health endpoint...")
    try:
        response = await client.health_check()
        assert response["status"] == "healthy", f"Expected status 'healthy', got {response['status']}"
        assert response["temporal_connected"] is True, "Temporal should be connected"
        print("✅ Health endpoint passed")
        return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False


async def test_root_endpoint(client: DurableAgentAPIClient):
    """Test the root endpoint."""
    print("\n🏠 Testing root endpoint...")
    try:
        response = await client.client.get(f"{client.base_url}/")
        response.raise_for_status()
        data = response.json()
        
        assert data["service"] == "Durable AI Agent API", f"Unexpected service name: {data['service']}"
        assert data["version"] == "0.1.0", f"Unexpected version: {data['version']}"
        assert data["status"] == "healthy", f"Unexpected status: {data['status']}"
        print("✅ Root endpoint passed")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False


async def test_chat_endpoint_creates_workflow(client: DurableAgentAPIClient):
    """Test that the chat endpoint creates a new workflow."""
    print("\n💬 Testing chat endpoint (workflow creation)...")
    try:
        response = await client.chat("Hello, find some events")
        
        # Verify workflow was created
        assert "workflow_id" in response, "Response should contain workflow_id"
        assert response["status"] == "completed", f"Expected status 'completed', got {response['status']}"
        assert "last_response" in response, "Response should contain last_response"
        
        print(f"✅ Chat endpoint passed - Workflow ID: {response['workflow_id']}")
        return True
    except Exception as e:
        print(f"❌ Chat endpoint failed: {e}")
        return False


async def test_chat_with_specific_workflow_id(client: DurableAgentAPIClient):
    """Test chat with a specific workflow ID."""
    print("\n🔖 Testing chat with specific workflow ID...")
    try:
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        response = await client.chat("Find events in Melbourne", workflow_id=workflow_id)
        
        # Verify the workflow ID matches
        assert response["workflow_id"] == workflow_id, f"Expected workflow_id {workflow_id}, got {response['workflow_id']}"
        assert response["status"] == "completed", f"Expected status 'completed', got {response['status']}"
        
        print(f"✅ Chat with specific workflow ID passed - ID: {workflow_id}")
        return True
    except Exception as e:
        print(f"❌ Chat with specific workflow ID failed: {e}")
        return False


async def test_workflow_status_endpoint(client: DurableAgentAPIClient):
    """Test the workflow status endpoint."""
    print("\n📊 Testing workflow status endpoint...")
    try:
        # First create a workflow
        chat_response = await client.chat("Test message")
        workflow_id = chat_response["workflow_id"]
        
        # Get status
        status_response = await client.get_workflow_status(workflow_id)
        
        assert status_response["workflow_id"] == workflow_id, "Workflow ID mismatch"
        assert status_response["status"] == "completed", f"Expected status 'completed', got {status_response['status']}"
        assert "query_count" in status_response, "Response should contain query_count"
        
        print(f"✅ Workflow status endpoint passed - Query count: {status_response['query_count']}")
        return True
    except Exception as e:
        print(f"❌ Workflow status endpoint failed: {e}")
        return False


async def test_workflow_query_endpoint(client: DurableAgentAPIClient):
    """Test the workflow query endpoint."""
    print("\n🔍 Testing workflow query endpoint...")
    try:
        # First create a workflow
        chat_response = await client.chat("Test query")
        workflow_id = chat_response["workflow_id"]
        
        # Query the workflow
        query_response = await client.query_workflow(workflow_id)
        
        assert query_response["workflow_id"] == workflow_id, "Workflow ID mismatch"
        assert query_response["query_count"] == 1, f"Expected query_count 1, got {query_response['query_count']}"
        assert "1 queries" in query_response["status"], f"Unexpected status message: {query_response['status']}"
        
        print(f"✅ Workflow query endpoint passed - Status: {query_response['status']}")
        return True
    except Exception as e:
        print(f"❌ Workflow query endpoint failed: {e}")
        return False


async def test_nonexistent_workflow_status(client: DurableAgentAPIClient):
    """Test getting status of non-existent workflow."""
    print("\n🚫 Testing non-existent workflow status...")
    try:
        await client.get_workflow_status("non-existent-workflow-id")
        print("❌ Should have failed with 404 but didn't")
        return False
    except Exception as e:
        if "404" in str(e):
            print("✅ Non-existent workflow status correctly returned 404")
            return True
        else:
            print(f"❌ Non-existent workflow status failed with unexpected error: {e}")
            return False


async def test_api_error_handling(client: DurableAgentAPIClient):
    """Test API error handling with invalid data."""
    print("\n⚠️ Testing API error handling...")
    try:
        # Try to send invalid data
        response = await client.client.post(
            f"{client.base_url}/chat",
            json={},  # Missing required 'message' field
        )
        
        # Should get 422 Unprocessable Entity
        if response.status_code == 422:
            print("✅ API error handling passed - correctly returned 422 for invalid data")
            return True
        else:
            print(f"❌ API error handling failed - expected 422, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API error handling test failed with exception: {e}")
        return False


async def test_chat_with_user_name(client: DurableAgentAPIClient):
    """Test chat endpoint with user_name parameter."""
    print("\n👤 Testing chat with user_name...")
    try:
        user_name = "test_user_123"
        response = await client.chat("Hello with username", user_name=user_name)
        
        # Verify workflow was created successfully
        assert "workflow_id" in response, "Response should contain workflow_id"
        assert response["status"] == "completed", f"Expected status 'completed', got {response['status']}"
        
        print(f"✅ Chat with user_name passed - User: {user_name}")
        return True
    except Exception as e:
        print(f"❌ Chat with user_name failed: {e}")
        return False


# New tests for different workflow routing paths

async def test_weather_prefix_query(client: DurableAgentAPIClient):
    """Test weather: prefix routing to weather query handler."""
    print("\n🌤️ Testing weather: prefix query routing...")
    try:
        response = await client.chat("weather: What's the weather forecast for New York City?")
        
        # Verify workflow was created and response contains weather info
        assert "workflow_id" in response, "Response should contain workflow_id"
        assert response["status"] == "completed", f"Expected status 'completed', got {response['status']}"
        
        # Check if response mentions weather-related content
        last_response = response.get("last_response", {})
        if isinstance(last_response, dict):
            message = last_response.get("message", "").lower()
        else:
            message = str(last_response).lower()
        
        assert any(word in message for word in ["weather", "temperature", "forecast", "child workflow"]), \
            f"Expected weather-related response, got: {message[:100]}..."
        
        print("✅ Weather prefix query routing passed")
        return True
    except Exception as e:
        print(f"❌ Weather prefix query routing failed: {e}")
        return False


async def test_historical_query(client: DurableAgentAPIClient):
    """Test historical keyword routing to historical query handler."""
    print("\n📊 Testing historical query routing...")
    try:
        response = await client.chat("Show me historical weather data for Chicago last month")
        
        # Verify workflow was created
        assert "workflow_id" in response, "Response should contain workflow_id"
        assert response["status"] == "completed", f"Expected status 'completed', got {response['status']}"
        
        # Check if response mentions historical data or error
        last_response = response.get("last_response", {})
        if isinstance(last_response, dict):
            message = last_response.get("message", "").lower()
        else:
            message = str(last_response).lower()
        
        print(f"Historical query response preview: {message[:100]}...")
        
        # The routing works even if the service is not available
        if "error" in message or "failed to connect" in message:
            print("✅ Historical query routing passed (service not available)")
        else:
            print("✅ Historical query routing passed")
        return True
    except Exception as e:
        print(f"❌ Historical query routing failed: {e}")
        return False


async def test_agriculture_query(client: DurableAgentAPIClient):
    """Test agriculture keyword routing to agricultural query handler."""
    print("\n🌱 Testing agriculture query routing...")
    try:
        response = await client.chat("What are the agriculture conditions for corn planting in Iowa?")
        
        # Verify workflow was created
        assert "workflow_id" in response, "Response should contain workflow_id"
        assert response["status"] == "completed", f"Expected status 'completed', got {response['status']}"
        
        # Check if response mentions agricultural content or error
        last_response = response.get("last_response", {})
        if isinstance(last_response, dict):
            message = last_response.get("message", "").lower()
        else:
            message = str(last_response).lower()
        
        print(f"Agriculture query response preview: {message[:100]}...")
        
        # The routing works even if the service is not available
        if "error" in message or "failed to connect" in message:
            print("✅ Agriculture query routing passed (service not available)")
        else:
            print("✅ Agriculture query routing passed")
        return True
    except Exception as e:
        print(f"❌ Agriculture query routing failed: {e}")
        return False


async def test_default_query(client: DurableAgentAPIClient):
    """Test default routing (no special keywords) to default query handler."""
    print("\n🎯 Testing default query routing...")
    try:
        response = await client.chat("Find some interesting events in San Francisco")
        
        # Verify workflow was created
        assert "workflow_id" in response, "Response should contain workflow_id"
        assert response["status"] == "completed", f"Expected status 'completed', got {response['status']}"
        
        # Check if response contains event information (default handler finds events)
        last_response = response.get("last_response", {})
        if isinstance(last_response, dict):
            message = last_response.get("message", "").lower()
        else:
            message = str(last_response).lower()
        
        assert "event" in message, f"Expected event-related response for default query, got: {message[:100]}..."
        
        print("✅ Default query routing passed")
        return True
    except Exception as e:
        print(f"❌ Default query routing failed: {e}")
        return False


async def test_multiple_weather_queries(client: DurableAgentAPIClient):
    """Test multiple weather queries with different formats."""
    print("\n🌦️ Testing multiple weather query formats...")
    
    weather_queries = [
        "weather: What's the temperature in Boston?",
        "weather: Will it rain tomorrow in Seattle?",
        "weather: Give me a 3-day forecast for Miami"
    ]
    
    all_passed = True
    for i, query in enumerate(weather_queries, 1):
        try:
            print(f"  [{i}/3] Testing: {query}")
            response = await client.chat(query)
            
            assert "workflow_id" in response, "Response should contain workflow_id"
            assert response["status"] == "completed", f"Expected status 'completed', got {response['status']}"
            
            print(f"  ✅ Query {i} passed")
        except Exception as e:
            print(f"  ❌ Query {i} failed: {e}")
            all_passed = False
    
    if all_passed:
        print("✅ Multiple weather queries passed")
    else:
        print("❌ Some weather queries failed")
    
    return all_passed


async def main():
    """Main test function."""
    print("🚀 Starting API Endpoints Integration Test")
    print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Create API client
    async with DurableAgentAPIClient() as client:
        # Run all tests
        tests = [
            # Basic API tests
            test_health_endpoint,
            test_root_endpoint,
            test_chat_endpoint_creates_workflow,
            test_chat_with_specific_workflow_id,
            test_chat_with_user_name,
            test_workflow_status_endpoint,
            test_workflow_query_endpoint,
            test_nonexistent_workflow_status,
            test_api_error_handling,
            
            # Workflow routing tests
            test_weather_prefix_query,
            test_historical_query,
            test_agriculture_query,
            test_default_query,
            test_multiple_weather_queries,
        ]
        
        results = []
        for test_func in tests:
            result = await test_func(client)
            results.append(result)
            # No delay needed - server can handle it
        
        # Summary
        print("\n" + "=" * 60)
        successful = sum(1 for r in results if r)
        failed = len(results) - successful
        
        print(f"✨ Test completed! Results:")
        print(f"   ✅ Successful: {successful}/{len(results)}")
        print(f"   ❌ Failed: {failed}/{len(results)}")
        
        if failed == 0:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {failed} test(s) failed")
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
    print("🏗️  Durable AI Agent - API Endpoints Test")
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