import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from temporalio import activity

from workflows.simple_agent_workflow import SimpleAgentWorkflow
from workflows.agentic_ai_workflow import AgenticAIWorkflow
from models.conversation import ConversationState, Message
from models.message_types import MessageType, ClassifiedMessage, classify_message
from models.types import ActivityStatus, ReactAgentActivityResult, ExtractAgentActivityResult, Response

# Mock activities for testing
@activity.defn(name="run_react_agent")
async def mock_react_agent_activity(user_message: str, iteration: int, trajectory: dict, user_name: str):
    """Mock react agent activity that returns finish immediately"""
    return ReactAgentActivityResult(
        status=ActivityStatus.SUCCESS,
        trajectory={
            **trajectory,
            f"thought_{iteration-1}": "I need to answer the user's question",
            f"tool_name_{iteration-1}": "finish",
            f"tool_args_{iteration-1}": {"answer": f"Mock response to: {user_message}"}
        },
        tool_name="finish",
        tool_args={"answer": f"Mock response to: {user_message}"},
        user_name=user_name
    )


@activity.defn(name="execute_tool")
async def mock_tool_execution_activity(tool_request):
    """Mock tool execution activity"""
    return {
        "status": ActivityStatus.SUCCESS,
        "trajectory": {
            **tool_request.trajectory,
            f"observation_{tool_request.current_iteration-1}": "Tool executed successfully"
        }
    }


@activity.defn(name="run_extract_agent")
async def mock_extract_agent_activity(trajectory: dict, user_query: str, user_name: str):
    """Mock extract agent activity"""
    return ExtractAgentActivityResult(
        status=ActivityStatus.SUCCESS,
        trajectory=trajectory,
        answer=f"Final answer for {user_name}: {user_query}",
        user_name=user_name
    )


@activity.defn(name="find_events_activity")
async def mock_find_events_activity(user_message: str, user_name: str):
    """Mock find events activity"""
    return {
        "message": f"Found events for {user_name}: {user_message}",
        "event_count": 3
    }


@activity.defn(name="weather_historical_activity")
async def mock_weather_historical_activity(user_message: str, user_name: str):
    """Mock historical weather activity"""
    return {
        "message": f"Historical weather data for {user_name}: {user_message}",
        "event_count": 1
    }


@activity.defn(name="agricultural_activity")
async def mock_agricultural_activity(user_message: str, user_name: str):
    """Mock agricultural activity"""
    return {
        "message": f"Agricultural data for {user_name}: {user_message}",
        "event_count": 1
    }


@pytest.mark.asyncio
class TestPhase2Interaction:
    """Tests for Phase 2 interaction features"""
    
    async def test_message_processing_loop(self):
        """Test that workflow processes messages from queue correctly"""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Register activities
            activities = [
                mock_react_agent_activity,
                mock_tool_execution_activity,
                mock_extract_agent_activity,
                mock_find_events_activity,
                mock_weather_historical_activity,
                mock_agricultural_activity
            ]
            
            async with Worker(
                env.client,
                task_queue="test-tq",
                workflows=[SimpleAgentWorkflow, AgenticAIWorkflow],
                activities=activities,
            ):
                # Start workflow with initial message
                handle = await env.client.start_workflow(
                    SimpleAgentWorkflow.run,
                    args=["Hello AI", "test-user"],
                    id="test-message-loop",
                    task_queue="test-tq",
                )
                
                # Wait for workflow to complete
                result = await handle.result()
                assert isinstance(result, Response)
                assert result.message is not None
                
                # Check conversation history
                history = await handle.query(SimpleAgentWorkflow.get_conversation_history)
                assert len(history) == 2  # Initial message + response
                
                # Verify message types
                user_messages = [m for m in history if m.actor == "user"]
                agent_messages = [m for m in history if m.actor == "agent"]
                assert len(user_messages) == 1
                assert len(agent_messages) == 1
    
    async def test_context_aware_agentic_workflow(self):
        """Test that AgenticAIWorkflow uses conversation context"""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Create conversation state with history
            conversation_state = ConversationState()
            conversation_state.add_message("user", "Tell me about Paris")
            conversation_state.add_message("agent", "Paris is the capital of France")
            conversation_state.add_message("user", "What about the weather there?")
            
            async with Worker(
                env.client,
                task_queue="test-tq",
                workflows=[AgenticAIWorkflow],
                activities=[
                    mock_react_agent_activity,
                    mock_tool_execution_activity,
                    mock_extract_agent_activity
                ],
            ):
                # Start workflow with conversation context
                handle = await env.client.start_workflow(
                    AgenticAIWorkflow.run,
                    args=["What's the temperature?", "test-user", conversation_state],
                    id="test-context-aware",
                    task_queue="test-tq",
                )
                
                result = await handle.result()
                assert isinstance(result, Response)
                assert result.message is not None
                
                # Check that trajectory includes conversation context
                trajectory = await handle.query(AgenticAIWorkflow.get_trajectory)
                assert "conversation_context" in trajectory
                assert len(trajectory["conversation_context"]) > 0
    
    async def test_message_classification(self):
        """Test message type classification"""
        # Test user query
        msg = classify_message("What's the weather today?")
        assert msg.message_type == MessageType.USER_QUERY
        assert msg.confidence == 0.8
        
        # Test system notification
        msg = classify_message("### System maintenance scheduled")
        assert msg.message_type == MessageType.SYSTEM_NOTIFICATION
        assert msg.confidence == 1.0
        assert "###" in msg.keywords_matched
        
        # Test tool confirmation
        msg = classify_message("yes")
        assert msg.message_type == MessageType.TOOL_CONFIRMATION
        assert msg.confidence == 1.0
        
        # Test summary request
        msg = classify_message("Can you summarize our conversation?")
        assert msg.message_type == MessageType.SUMMARY_REQUEST
        assert msg.confidence == 0.9
        assert "summarize" in msg.keywords_matched
    
    async def test_workflow_status_during_processing(self):
        """Test workflow status updates during message processing"""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-tq",
                workflows=[SimpleAgentWorkflow],
                activities=[mock_find_events_activity],
            ):
                # Start workflow
                handle = await env.client.start_workflow(
                    SimpleAgentWorkflow.run,
                    args=["Test message", "test-user"],
                    id="test-status",
                    task_queue="test-tq",
                )
                
                # Wait for workflow to complete
                result = await handle.result()
                
                # Check final status
                status = await handle.query(SimpleAgentWorkflow.get_workflow_status)
                assert not status.is_processing  # Should be done processing
                assert not status.should_end
                assert status.message_count == 2  # User message + agent response
    
    async def test_multiple_message_routing(self):
        """Test that different message types are routed correctly"""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-tq",
                workflows=[SimpleAgentWorkflow, AgenticAIWorkflow],
                activities=[
                    mock_react_agent_activity,
                    mock_tool_execution_activity,
                    mock_extract_agent_activity,
                    mock_find_events_activity,
                    mock_weather_historical_activity,
                    mock_agricultural_activity
                ],
            ):
                # Test different message types with separate workflow executions
                test_cases = [
                    ("Find some events", "events"),
                    ("Show historical data", "historical"),
                    ("agriculture information", "agricultural"),
                    ("weather: Current conditions", "weather")
                ]
                
                for i, (message, expected_keyword) in enumerate(test_cases):
                    # Start new workflow for each message type
                    handle = await env.client.start_workflow(
                        SimpleAgentWorkflow.run,
                        args=[message, "test-user"],
                        id=f"test-routing-{i}",
                        task_queue="test-tq",
                    )
                    
                    # Wait for completion
                    result = await handle.result()
                    
                    # Verify routing worked correctly
                    # Weather queries use AgenticAIWorkflow which returns differently
                    if message.startswith("weather:"):
                        assert "answer" in result.message.lower() or "final" in result.message.lower()
                    else:
                        assert expected_keyword in result.message.lower()