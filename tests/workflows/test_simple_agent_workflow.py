import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from workflows.simple_agent_workflow import SimpleAgentWorkflow
from models.conversation import ConversationState, Message
from models.workflow_models import WorkflowStatus


@pytest.mark.asyncio
class TestSimpleAgentWorkflow:
    """Test SimpleAgentWorkflow signal and query handlers"""
    
    async def test_signal_handlers(self):
        """Test that signal handlers work correctly"""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-tq",
                workflows=[SimpleAgentWorkflow],
            ):
                # Start workflow
                handle = await env.client.start_workflow(
                    SimpleAgentWorkflow.run,
                    args=["Initial message", "test-user"],
                    id="test-signals",
                    task_queue="test-tq",
                )
                
                # Test user message signal
                await handle.signal(SimpleAgentWorkflow.user_message, "Hello AI")
                
                # Query workflow status
                status = await handle.query(SimpleAgentWorkflow.get_workflow_status)
                assert status.pending_messages == 1
                assert not status.should_end
                
                # Test end conversation signal
                await handle.signal(SimpleAgentWorkflow.end_conversation)
                status = await handle.query(SimpleAgentWorkflow.get_workflow_status)
                assert status.should_end == True
                
                # Test request summary signal
                await handle.signal(SimpleAgentWorkflow.request_summary)
                # The workflow should handle the signal without error
    
    async def test_query_handlers(self):
        """Test that query handlers return correct information"""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-tq",
                workflows=[SimpleAgentWorkflow],
            ):
                # Start workflow
                handle = await env.client.start_workflow(
                    SimpleAgentWorkflow.run,
                    args=["Test message", "test-user"],
                    id="test-queries",
                    task_queue="test-tq",
                )
                
                # Test get_conversation_history query
                history = await handle.query(SimpleAgentWorkflow.get_conversation_history)
                assert isinstance(history, list)
                # Should have the initial message
                assert len(history) >= 1
                
                # Test get_workflow_status query
                status = await handle.query(SimpleAgentWorkflow.get_workflow_status)
                assert isinstance(status, WorkflowStatus)
                assert status.message_count >= 1  # Initial message
                assert status.pending_messages >= 0
                assert status.interaction_count >= 1
                assert isinstance(status.is_processing, bool)
                assert status.should_end == False
                
                # Test get_current_reasoning query
                reasoning = await handle.query(SimpleAgentWorkflow.get_current_reasoning)
                assert isinstance(reasoning, dict)
                assert len(reasoning) == 0  # Initially empty
                
                # Test existing query handlers
                query_count = await handle.query(SimpleAgentWorkflow.get_query_count)
                assert query_count == 1  # One query from initial message
                
                status_str = await handle.query(SimpleAgentWorkflow.get_status)
                assert "Workflow has processed 1 queries" in status_str
    
    async def test_message_queue_handling(self):
        """Test message queue functionality"""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-tq",
                workflows=[SimpleAgentWorkflow],
            ):
                # Start workflow
                handle = await env.client.start_workflow(
                    SimpleAgentWorkflow.run,
                    args=["Start", "test-user"],
                    id="test-queue",
                    task_queue="test-tq",
                )
                
                # Add multiple messages to queue
                await handle.signal(SimpleAgentWorkflow.user_message, "Message 1")
                await handle.signal(SimpleAgentWorkflow.user_message, "Message 2")
                await handle.signal(SimpleAgentWorkflow.user_message, "Message 3")
                
                # Check queue status
                status = await handle.query(SimpleAgentWorkflow.get_workflow_status)
                assert status.pending_messages == 3
                
                # Check conversation history shows initial message
                history = await handle.query(SimpleAgentWorkflow.get_conversation_history)
                assert any(msg.content == "Start" for msg in history)