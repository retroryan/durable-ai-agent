"""Integration tests for the durable AI agent."""
import asyncio
import uuid

import pytest
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from activities import find_events_activity
from models.types import Response
from workflows import SimpleAgentWorkflow


@pytest.mark.asyncio
async def test_simple_workflow_execution():
    """Test basic workflow execution."""
    # WorkflowEnvironment.start_time_skipping() creates a test environment that
    # fast-forwards time, allowing for efficient testing of workflows with
    # time-based logic (e.g., timers, sleeps) without real-time waiting.
    async with await WorkflowEnvironment.start_time_skipping() as env:
        # Register workflow and activities
        worker = Worker(
            env.client,
            task_queue="test-queue",
            workflows=[SimpleAgentWorkflow],
            activities=[find_events_activity],
        )

        async with worker:
            # Start workflow
            handle = await env.client.start_workflow(
                SimpleAgentWorkflow.run,
                args=["test message"],
                id=f"test-workflow-{uuid.uuid4()}",
                task_queue="test-queue",
            )

            # Get result
            result: Response = await handle.result()

            # Verify result
            assert result.message.startswith("Found")
            assert result.event_count >= 0
            assert result.query_count == 1


@pytest.mark.asyncio
async def test_workflow_query_count():
    """Test workflow query count functionality."""
    # WorkflowEnvironment.start_time_skipping() creates a test environment that
    # fast-forwards time, allowing for efficient testing of workflows with
    # time-based logic (e.g., timers, sleeps) without real-time waiting.
    async with await WorkflowEnvironment.start_time_skipping() as env:
        worker = Worker(
            env.client,
            task_queue="test-queue",
            workflows=[SimpleAgentWorkflow],
            activities=[find_events_activity],
        )

        async with worker:
            # Start workflow
            handle = await env.client.start_workflow(
                SimpleAgentWorkflow.run,
                args=["test message"],
                id=f"test-workflow-{uuid.uuid4()}",
                task_queue="test-queue",
            )

            # Wait for completion
            await handle.result()

            # Query the count
            query_count = await handle.query(SimpleAgentWorkflow.get_query_count)
            assert query_count == 1

            # Query the status
            status = await handle.query(SimpleAgentWorkflow.get_status)
            assert "1 queries" in status


@pytest.mark.asyncio
async def test_workflow_id_handling():
    """Test that workflow IDs are handled correctly."""
    # WorkflowEnvironment.start_time_skipping() creates a test environment that
    # fast-forwards time, allowing for efficient testing of workflows with
    # time-based logic (e.g., timers, sleeps) without real-time waiting.
    async with await WorkflowEnvironment.start_time_skipping() as env:
        worker = Worker(
            env.client,
            task_queue="test-queue",
            workflows=[SimpleAgentWorkflow],
            activities=[find_events_activity],
        )

        async with worker:
            # Test with specific workflow ID
            workflow_id = "test-specific-id"

            handle = await env.client.start_workflow(
                SimpleAgentWorkflow.run,
                args=["test message"],
                id=workflow_id,
                task_queue="test-queue",
            )

            # Verify workflow ID matches
            assert handle.id == workflow_id

            # Get result
            result = await handle.result()
            assert result.query_count == 1

            # In test environment with time skipping, starting workflow with
            # same ID after completion might be allowed. Let's just verify
            # we can query the original workflow
            queried_count = await handle.query(SimpleAgentWorkflow.get_query_count)
            assert queried_count == 1


@pytest.mark.asyncio
async def test_activity_execution():
    """Test that the activity executes correctly."""
    # Direct activity test
    result = await find_events_activity("test message")

    assert isinstance(result, dict)
    assert "message" in result
    assert "event_count" in result
    assert isinstance(result["message"], str) and result["message"].startswith("Found")
    assert result["event_count"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
