"""Integration tests for API endpoints."""
import pytest
from utils.test_helpers import WorkflowAssertions


@pytest.mark.api
class TestAPIEndpoints:
    """Test basic API endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_client):
        """Test the health check endpoint."""
        response = await api_client.health_check()

        assert response["status"] == "healthy"
        assert response["temporal_connected"] is True

    @pytest.mark.asyncio
    async def test_root_endpoint(self, api_client):
        """Test the root endpoint."""
        response = await api_client.client.get(f"{api_client.base_url}/")
        response.raise_for_status()
        data = response.json()

        assert data["service"] == "Durable AI Agent API"
        assert data["version"] == "0.1.0"
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_chat_endpoint_creates_workflow(self, api_client):
        """Test that the chat endpoint creates a new workflow."""
        response = await api_client.chat("Hello, find some events")

        # Verify workflow was created
        WorkflowAssertions.assert_workflow_started(response)
        WorkflowAssertions.assert_workflow_completed(response)
        WorkflowAssertions.assert_events_found(response)

    @pytest.mark.asyncio
    async def test_chat_with_specific_workflow_id(self, api_client, fresh_workflow_id):
        """Test chat with a specific workflow ID."""
        response = await api_client.chat(
            "Find events in Melbourne",
            workflow_id=fresh_workflow_id,
        )

        # Verify the workflow ID matches
        assert response["workflow_id"] == fresh_workflow_id
        WorkflowAssertions.assert_workflow_completed(response)

    @pytest.mark.asyncio
    async def test_workflow_status_endpoint(self, api_client):
        """Test the workflow status endpoint."""
        # First create a workflow
        chat_response = await api_client.chat("Test message")
        workflow_id = WorkflowAssertions.get_workflow_id(chat_response)

        # Get status
        status_response = await api_client.get_workflow_status(workflow_id)

        assert status_response["workflow_id"] == workflow_id
        assert status_response["status"] == "completed"
        assert "query_count" in status_response

    @pytest.mark.asyncio
    async def test_workflow_query_endpoint(self, api_client):
        """Test the workflow query endpoint."""
        # First create a workflow
        chat_response = await api_client.chat("Test query")
        workflow_id = WorkflowAssertions.get_workflow_id(chat_response)

        # Query the workflow
        query_response = await api_client.query_workflow(workflow_id)

        assert query_response["workflow_id"] == workflow_id
        assert query_response["query_count"] == 1
        assert "1 queries" in query_response["status"]

    @pytest.mark.asyncio
    async def test_nonexistent_workflow_status(self, api_client):
        """Test getting status of non-existent workflow."""
        with pytest.raises(Exception) as exc_info:
            await api_client.get_workflow_status("non-existent-workflow-id")

        # Should get 404
        assert "404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_error_handling(self, api_client):
        """Test API error handling with invalid data."""
        # Try to send invalid data
        response = await api_client.client.post(
            f"{api_client.base_url}/chat",
            json={},  # Missing required 'message' field
        )

        # Should get 422 Unprocessable Entity
        assert response.status_code == 422
