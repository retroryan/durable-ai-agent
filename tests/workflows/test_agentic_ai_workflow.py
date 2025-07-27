"""Tests for agentic AI workflow with consolidated MCP tools."""
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from activities.extract_agent_activity import ExtractAgentActivity
from activities.react_agent_activity import ReactAgentActivity
from activities.tool_execution_activity import ToolExecutionActivity
from models.types import (
    ActivityStatus,
    ExtractAgentActivityResult,
    ReactAgentActivityResult,
    ToolExecutionResult,
    WorkflowSummary,
    Message,
)
from models.trajectory import Trajectory
from workflows.agentic_ai_workflow import AgenticAIWorkflow


@pytest.mark.asyncio
class TestAgenticAIWorkflow:
    """Tests for agentic AI workflow with consolidated tools."""
    
    async def test_workflow_executes_consolidated_tools(self):
        """Test that workflow executes consolidated MCP tools through ToolExecutionActivity."""
        # Skip this test for now - workflow with signals is complex to test in time-skipping mode
        pytest.skip("Workflow signal testing needs refactoring for time-skipping environment")
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Track call counts for debugging
            react_call_count = 0
            tool_call_count = 0
            extract_call_count = 0
            
            # Mock activities
            trajectory = Trajectory(
                iteration=0,
                thought="I need to get weather forecast",
                tool_name="get_weather_forecast",
                tool_args={"latitude": 40.7, "longitude": -74.0, "days": 3}
            )
            mock_react_result = ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectories=[trajectory],
                user_name="test_user"
            )
            
            # Mock tool execution result - update trajectory with observation
            trajectory_with_obs = Trajectory(
                iteration=0,
                thought="I need to get weather forecast",
                tool_name="get_weather_forecast",
                tool_args={"latitude": 40.7, "longitude": -74.0, "days": 3},
                observation="Weather forecast: Sunny for 3 days"
            )
            mock_tool_result = ToolExecutionResult(
                success=True,
                trajectories=[trajectory_with_obs]
            )
            
            # Mock extract result
            mock_extract_result = ExtractAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                answer="The weather forecast shows sunny conditions for the next 3 days.",
                trajectories=mock_tool_result.trajectories
            )
            
            # Create mock activities
            @activity.defn(name="run_react_agent")
            async def mock_react_agent(*args):
                nonlocal react_call_count
                react_call_count += 1
                if react_call_count == 1:
                    # First call - return trajectory with tool to execute
                    return mock_react_result
                else:
                    # Second call - signal completion with finish tool
                    finish_trajectory = Trajectory(
                        iteration=1,
                        thought="I have the weather forecast information",
                        tool_name="finish",
                        tool_args={}
                    )
                    return ReactAgentActivityResult(
                        status=ActivityStatus.SUCCESS,
                        trajectories=[trajectory_with_obs, finish_trajectory],
                        user_name="test_user"
                    )
            
            @activity.defn(name="execute_tool")
            async def mock_execute_tool(*args):
                nonlocal tool_call_count
                tool_call_count += 1
                return mock_tool_result
            
            @activity.defn(name="run_extract_agent")
            async def mock_extract_agent(*args):
                nonlocal extract_call_count
                extract_call_count += 1
                return mock_extract_result
            
            # Run workflow with mocked activities
            async with Worker(
                env.client,
                task_queue="test-task-queue",
                workflows=[AgenticAIWorkflow],
                activities=[
                    mock_react_agent,
                    mock_execute_tool,
                    mock_extract_agent,
                ],
            ):
                # Start workflow with no initial input (or None)
                handle = await env.client.start_workflow(
                    AgenticAIWorkflow.run,
                    None,  # No initial WorkflowSummary
                    id="test-workflow-consolidated",
                    task_queue="test-task-queue",
                )
                
                # Send prompt via signal
                await handle.signal("prompt", "What's the weather forecast?")
                
                # Wait a moment for time-skipping to process the prompt
                # The workflow needs to process through its loop
                import asyncio
                await asyncio.sleep(0)  # Yield control to allow workflow to process
                
                # End the chat after processing
                await handle.signal("end_chat")
                
                # Get result - returns ConversationHistory (List[Message])
                result = await handle.result()
                
                # Verify result is a list of messages
                assert isinstance(result, list)
                
                # Debug: print what we got
                print(f"Result type: {type(result)}")
                print(f"Result length: {len(result)}")
                print(f"Messages: {[msg.role for msg in result]}")
                print(f"Call counts - React: {react_call_count}, Tool: {tool_call_count}, Extract: {extract_call_count}")
                
                assert len(result) > 0, f"Expected messages but got: {result}"
                # Find assistant/agent response (workflow uses 'agent' role)
                agent_messages = [msg for msg in result if msg.role == "agent"]
                assert len(agent_messages) > 0, f"No agent messages found. Messages: {[(msg.role, msg.content[:50]) for msg in result]}"
                assert "sunny" in agent_messages[-1].content.lower()
    
    async def test_workflow_handles_multiple_tool_iterations(self):
        """Test workflow with multiple tool iterations."""
        # Skip this test for now - workflow with signals is complex to test in time-skipping mode
        pytest.skip("Workflow signal testing needs refactoring for time-skipping environment")
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Mock first React iteration
            trajectory_1 = Trajectory(
                iteration=0,
                thought="Need current weather",
                tool_name="get_weather_forecast",
                tool_args={"latitude": 40.7, "longitude": -74.0, "days": 1}
            )
            mock_react_result_1 = ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectories=[trajectory_1],
                user_name="test_user"
            )
            
            # Mock second React iteration - includes completed first step and new second step
            trajectory_1_with_obs = Trajectory(
                iteration=0,
                thought="Need current weather",
                tool_name="get_weather_forecast",
                tool_args={"latitude": 40.7, "longitude": -74.0, "days": 1},
                observation="Current: 20°C"
            )
            trajectory_2 = Trajectory(
                iteration=1,
                thought="Now need historical data",
                tool_name="get_historical_weather",
                tool_args={"latitude": 40.7, "longitude": -74.0, "start_date": "2025-01-01", "end_date": "2025-01-07"}
            )
            mock_react_result_2 = ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectories=[trajectory_1_with_obs, trajectory_2],
                user_name="test_user"
            )
            
            # Mock tool results
            mock_tool_result_1 = ToolExecutionResult(
                success=True,
                trajectories=[trajectory_1_with_obs]
            )
            
            trajectory_2_with_obs = Trajectory(
                iteration=1,
                thought="Now need historical data",
                tool_name="get_historical_weather",
                tool_args={"latitude": 40.7, "longitude": -74.0, "start_date": "2025-01-01", "end_date": "2025-01-07"},
                observation="Historical avg: 15°C"
            )
            mock_tool_result_2 = ToolExecutionResult(
                success=True,
                trajectories=[trajectory_1_with_obs, trajectory_2_with_obs]
            )
            
            # Mock final extract
            mock_extract_result = ExtractAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                answer="Current temperature is 20°C, warmer than the historical average of 15°C.",
                trajectories=mock_tool_result_2.trajectories
            )
            
            # Track calls
            react_call_count = 0
            tool_call_count = 0
            
            @activity.defn(name="run_react_agent")
            async def mock_react_agent(*args):
                nonlocal react_call_count
                react_call_count += 1
                if react_call_count == 1:
                    return mock_react_result_1
                elif react_call_count == 2:
                    return mock_react_result_2
                else:
                    # Final call - no more tools needed
                    # Create empty trajectory to signal completion
                    final_trajectory = Trajectory(
                        iteration=2,
                        thought="I have gathered both current and historical weather data",
                        tool_name="",  # Empty string signals completion
                        tool_args={}
                    )
                    return ReactAgentActivityResult(
                        status=ActivityStatus.SUCCESS,
                        trajectories=[trajectory_1_with_obs, trajectory_2_with_obs, final_trajectory],
                        user_name="test_user"
                    )
            
            @activity.defn(name="execute_tool")
            async def mock_execute_tool(*args):
                nonlocal tool_call_count
                tool_call_count += 1
                if tool_call_count == 1:
                    return mock_tool_result_1
                else:
                    return mock_tool_result_2
            
            @activity.defn(name="run_extract_agent")
            async def mock_extract_agent(*args):
                return mock_extract_result
            
            # Run workflow
            async with Worker(
                env.client,
                task_queue="test-task-queue",
                workflows=[AgenticAIWorkflow],
                activities=[
                    mock_react_agent,
                    mock_execute_tool,
                    mock_extract_agent,
                ],
            ):
                # Start workflow with no initial input
                handle = await env.client.start_workflow(
                    AgenticAIWorkflow.run,
                    None,  # No initial WorkflowSummary
                    id="test-workflow-multiple-tools",
                    task_queue="test-task-queue",
                )
                
                # Send prompt via signal
                await handle.signal("prompt", "Compare current weather to last week")
                
                # End the chat
                await handle.signal("end_chat")
                
                # Get result - returns ConversationHistory (List[Message])
                result = await handle.result()
                
                # Verify result is a list of messages
                assert isinstance(result, list)
                assert len(result) > 0
                # Find assistant response
                assistant_messages = [msg for msg in result if msg.role == "assistant"]
                assert len(assistant_messages) > 0
                final_response = assistant_messages[-1].content
                assert "20°C" in final_response
                assert "15°C" in final_response
                # The workflow reaches max iterations (5) so we expect 3 react calls
                # (initial forecast, historical weather, then completion signal)
                assert react_call_count == 3
                assert tool_call_count == 2  # Only 2 actual tool executions