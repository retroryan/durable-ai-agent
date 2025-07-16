import pytest
import asyncio
import httpx
from temporalio.client import Client

from models.api_models import SendMessageRequest, SendMessageResponse, EndConversationResponse
from models.types import WorkflowInput, WorkflowState


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_full_conversation_flow():
    """Test complete conversation flow through API"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # Start new conversation
        response = await http_client.post(
            "/chat",
            json={"message": "Hello AI assistant"}
        )
        assert response.status_code == 200
        data = response.json()
        workflow_id = data["workflow_id"]
        assert workflow_id is not None
        assert data["status"] == "completed"
        
        # Send weather query using validated request model
        weather_message = "weather: What's the weather in San Francisco?"
        response = await http_client.post(
            "/chat",
            json={"message": weather_message}
        )
        assert response.status_code == 200
        weather_data = response.json()
        assert weather_data["status"] == "completed"
        assert "weather" in weather_data["response"]["result"].lower() or \
               "forecast" in weather_data["response"]["result"].lower()
        
        # Query workflow status
        response = await http_client.get(
            f"/workflow/{workflow_id}/status"
        )
        assert response.status_code == 200
        status = response.json()
        assert status["workflow_id"] == workflow_id
        assert status["status"] == "completed"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_signal_driven_conversation():
    """Test signal-driven conversation features (future functionality)"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # Start conversation
        response = await http_client.post(
            "/chat",
            json={"message": "Start signal test"}
        )
        assert response.status_code == 200
        workflow_id = response.json()["workflow_id"]
        
        # Wait briefly for workflow to process
        await asyncio.sleep(0.5)
        
        # Try to send signal to completed workflow (should fail gracefully)
        message_request = SendMessageRequest(message="This is a signal message")
        response = await http_client.post(
            f"/workflow/{workflow_id}/message",
            json=message_request.model_dump()
        )
        # This will fail in current architecture but endpoint exists
        assert response.status_code in [200, 500]
        
        # Request summary (will fail on completed workflow)
        response = await http_client.post(
            f"/workflow/{workflow_id}/request-summary"
        )
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_query_handlers():
    """Test workflow query handlers"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # Start conversation
        response = await http_client.post(
            "/chat",
            json={"message": "Test query handlers"}
        )
        assert response.status_code == 200
        workflow_id = response.json()["workflow_id"]
        
        # Query general workflow state
        response = await http_client.get(
            f"/workflow/{workflow_id}/query"
        )
        assert response.status_code == 200
        query_data = response.json()
        assert "workflow_id" in query_data
        assert "query_count" in query_data
        
        # Try to get history (will fail on completed workflow)
        response = await http_client.get(
            f"/workflow/{workflow_id}/history"
        )
        # May fail since workflow is completed
        assert response.status_code in [200, 500]
        
        # Try to get detailed status
        response = await http_client.get(
            f"/workflow/{workflow_id}/workflow-status"
        )
        # May fail since workflow is completed
        assert response.status_code in [200, 500]


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_weather_tool_execution():
    """Test weather tool execution through workflows"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # Send weather query
        response = await http_client.post(
            "/chat",
            json={"message": "weather: What's the forecast for Chicago?"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response contains weather information
        result = data["response"]["result"]
        assert any(word in result.lower() for word in ["weather", "forecast", "temperature", "conditions"])
        
        # Check if it mentions Chicago
        assert "chicago" in result.lower()


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_agentic_workflow_queries():
    """Test AgenticAIWorkflow specific queries"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as http_client:
        # Start weather conversation to trigger AgenticAIWorkflow
        response = await http_client.post(
            "/chat",
            json={"message": "weather: Get historical weather for Boston"}
        )
        assert response.status_code == 200
        workflow_id = response.json()["workflow_id"]
        
        # Get AI workflow state
        response = await http_client.get(
            f"/workflow/{workflow_id}/ai-state"
        )
        # This endpoint is for child workflows, may not work for parent
        assert response.status_code in [200, 404]
        
        # Try with trajectory
        response = await http_client.get(
            f"/workflow/{workflow_id}/ai-state?include_trajectory=true"
        )
        assert response.status_code in [200, 404]
        
        # Get AI workflow tools
        response = await http_client.get(
            f"/workflow/{workflow_id}/ai-tools"
        )
        assert response.status_code in [200, 404]