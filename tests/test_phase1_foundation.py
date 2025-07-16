import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from workflows.simple_agent_workflow import SimpleAgentWorkflow
from models.conversation import ConversationState, Message
from models.workflow_models import WorkflowStatus


@pytest.mark.asyncio
async def test_signal_handlers():
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


@pytest.mark.asyncio
async def test_query_handlers():
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


@pytest.mark.asyncio 
async def test_conversation_state_model():
    """Test the ConversationState model functionality"""
    state = ConversationState()
    
    # Test initial state
    assert len(state.messages) == 0
    assert state.interaction_count == 0
    assert state.summary_requested == False
    assert state.summary is None
    
    # Test adding messages
    state.add_message("user", "Hello")
    assert len(state.messages) == 1
    assert state.interaction_count == 1
    assert state.messages[0].actor == "user"
    assert state.messages[0].content == "Hello"
    
    state.add_message("agent", "Hi there!")
    assert len(state.messages) == 2
    assert state.interaction_count == 2
    
    # Test message validation
    with pytest.raises(ValueError):
        # Test message content too long
        state.add_message("user", "x" * 50001)


@pytest.mark.asyncio
async def test_message_model():
    """Test the Message model validation"""
    # Valid message
    msg = Message(actor="user", content="Test message")
    assert msg.actor == "user"
    assert msg.content == "Test message"
    assert msg.timestamp is not None
    assert isinstance(msg.metadata, dict)
    
    # Test actor validation
    with pytest.raises(ValueError):
        Message(actor="invalid", content="Test")
    
    # Test content validation
    with pytest.raises(ValueError):
        Message(actor="user", content="")
    
    with pytest.raises(ValueError):
        Message(actor="user", content="x" * 50001)


@pytest.mark.asyncio
async def test_workflow_status_model():
    """Test the WorkflowStatus model"""
    status = WorkflowStatus(
        is_processing=True,
        should_end=False,
        message_count=5,
        pending_messages=2,
        interaction_count=7
    )
    
    assert status.is_processing == True
    assert status.should_end == False
    assert status.message_count == 5
    assert status.pending_messages == 2
    assert status.interaction_count == 7
    
    # Test validation
    with pytest.raises(ValueError):
        WorkflowStatus(
            is_processing=True,
            should_end=False,
            message_count=-1,  # Negative count not allowed
            pending_messages=0,
            interaction_count=0
        )