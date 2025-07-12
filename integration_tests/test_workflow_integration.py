"""Integration tests for workflow functionality."""
import asyncio

import pytest
from utils.test_helpers import WorkflowAssertions


@pytest.mark.workflow
class TestWorkflowIntegration:
    """Test workflow functionality through the API."""

    @pytest.mark.asyncio
    async def test_workflow_executes_activity(self, api_client):
        """Test that workflow executes the find_events activity."""
        response = await api_client.chat("Find some events")

        # Verify activity was executed
        WorkflowAssertions.assert_workflow_completed(response)
        WorkflowAssertions.assert_events_found(response)

        # Verify we got a proper response
        message = response["last_response"]["message"]
        assert "found" in message.lower()
        assert "events in Melbourne" in message

    @pytest.mark.asyncio
    async def test_workflow_query_count_persistence(self, api_client):
        """Test that workflow maintains query count state."""
        # Create first workflow
        response1 = await api_client.chat("First query")
        workflow_id = WorkflowAssertions.get_workflow_id(response1)

        # Query count should be 1
        assert WorkflowAssertions.get_query_count(response1) == 1

        # Create another workflow (new ID)
        response2 = await api_client.chat("Second query")

        # New workflow should also have query count 1
        assert WorkflowAssertions.get_query_count(response2) == 1

        # Original workflow should still have count 1
        query_response = await api_client.query_workflow(workflow_id)
        assert query_response["query_count"] == 1

    @pytest.mark.asyncio
    async def test_multiple_workflows_isolation(self, api_client):
        """Test that multiple workflows are isolated from each other."""
        # Start multiple workflows
        workflows = []
        for i in range(3):
            response = await api_client.chat(f"Query {i}")
            workflows.append(
                {
                    "id": WorkflowAssertions.get_workflow_id(response),
                    "index": i,
                }
            )

        # Verify each workflow is independent
        for workflow in workflows:
            query_response = await api_client.query_workflow(workflow["id"])
            assert query_response["query_count"] == 1
            assert query_response["workflow_id"] == workflow["id"]

    @pytest.mark.asyncio
    async def test_workflow_with_custom_id(self, api_client):
        """Test creating workflow with custom ID."""
        custom_id = "my-custom-workflow-123"

        response = await api_client.chat(
            "Find events with custom ID",
            workflow_id=custom_id,
        )

        assert response["workflow_id"] == custom_id
        WorkflowAssertions.assert_workflow_completed(response)

        # Verify we can query it
        query_response = await api_client.query_workflow(custom_id)
        assert query_response["workflow_id"] == custom_id

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_workflow_retry_behavior(self, api_client):
        """Test workflow behavior with retries (simulated)."""
        # Our workflow has retry policy with 3 attempts
        # In production, this would test actual retry behavior
        # For now, we just verify the workflow completes successfully

        response = await api_client.chat("Test retry behavior")
        WorkflowAssertions.assert_workflow_completed(response)

        # Verify the activity executed successfully
        assert response["last_response"]["event_count"] >= 0

    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, api_client):
        """Test multiple workflows executing concurrently."""
        # Start multiple workflows concurrently
        tasks = []
        for i in range(5):
            task = api_client.chat(f"Concurrent query {i}")
            tasks.append(task)

        # Wait for all to complete
        responses = await asyncio.gather(*tasks)

        # Verify all completed successfully
        workflow_ids = set()
        for response in responses:
            WorkflowAssertions.assert_workflow_completed(response)
            workflow_id = WorkflowAssertions.get_workflow_id(response)
            workflow_ids.add(workflow_id)

        # All workflow IDs should be unique
        assert len(workflow_ids) == 5

    @pytest.mark.asyncio
    async def test_workflow_response_format(self, api_client):
        """Test the workflow response format is consistent."""
        response = await api_client.chat("Check response format")

        # Check top-level fields
        assert "workflow_id" in response
        assert "status" in response
        assert "query_count" in response
        assert "last_response" in response

        # Check nested response fields
        last_response = response["last_response"]
        assert "message" in last_response
        assert "event_count" in last_response
        assert "query_count" in last_response

        # Verify types
        assert isinstance(response["workflow_id"], str)
        assert isinstance(response["status"], str)
        assert isinstance(response["query_count"], int)
        assert isinstance(last_response["message"], str)
        assert isinstance(last_response["event_count"], int)
        assert isinstance(last_response["query_count"], int)
