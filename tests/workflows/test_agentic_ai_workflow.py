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
)
from workflows.agentic_ai_workflow import AgenticAIWorkflow


@pytest.mark.asyncio
class TestAgenticAIWorkflow:
    """Tests for agentic AI workflow with consolidated tools."""
    
    async def test_workflow_executes_consolidated_tools(self):
        """Test that workflow executes consolidated MCP tools through ToolExecutionActivity."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Mock activities
            mock_react_result = ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectory={
                    "thought_0": "I need to get weather forecast",
                    "tool_name_0": "get_weather_forecast",
                    "tool_args_0": {"latitude": 40.7, "longitude": -74.0, "days": 3},
                },
                tool_name="get_weather_forecast",
                tool_args={"latitude": 40.7, "longitude": -74.0, "days": 3},
                user_name="test_user"
            )
            
            # Mock tool execution result
            mock_tool_result = {
                "status": ActivityStatus.SUCCESS,
                "trajectory": {
                    "thought_0": "I need to get weather forecast",
                    "tool_name_0": "get_weather_forecast", 
                    "tool_args_0": {"latitude": 40.7, "longitude": -74.0, "days": 3},
                    "observation_0": "Weather forecast: Sunny for 3 days"
                }
            }
            
            # Mock extract result
            mock_extract_result = ExtractAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                answer="The weather forecast shows sunny conditions for the next 3 days.",
                trajectory=mock_tool_result["trajectory"]
            )
            
            # Create mock activities
            @activity.defn(name="run_react_agent")
            async def mock_react_agent(*args):
                return mock_react_result
            
            @activity.defn(name="execute_tool")
            async def mock_execute_tool(*args):
                return mock_tool_result
            
            @activity.defn(name="run_extract_agent")
            async def mock_extract_agent(*args):
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
                # Start workflow
                handle = await env.client.start_workflow(
                    AgenticAIWorkflow.run,
                    {"user_query": "What's the weather forecast?", "user_name": "test_user"},
                    id="test-workflow-consolidated",
                    task_queue="test-task-queue",
                )
                
                # Get result
                result = await handle.result()
                
                # Verify result is a Response object
                assert result.message
                assert "sunny" in result.message.lower()
                assert result.query_count >= 1
    
    async def test_workflow_handles_multiple_tool_iterations(self):
        """Test workflow with multiple tool iterations."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Mock first React iteration
            mock_react_result_1 = ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectory={
                    "thought_0": "Need current weather",
                    "tool_name_0": "get_weather_forecast",
                    "tool_args_0": {"latitude": 40.7, "longitude": -74.0, "days": 1},
                },
                tool_name="get_weather_forecast",
                tool_args={"latitude": 40.7, "longitude": -74.0, "days": 1},
                user_name="test_user"
            )
            
            # Mock second React iteration
            mock_react_result_2 = ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectory={
                    "thought_0": "Need current weather",
                    "tool_name_0": "get_weather_forecast",
                    "tool_args_0": {"latitude": 40.7, "longitude": -74.0, "days": 1},
                    "observation_0": "Current: 20°C",
                    "thought_1": "Now need historical data",
                    "tool_name_1": "get_historical_weather",
                    "tool_args_1": {"latitude": 40.7, "longitude": -74.0, "start_date": "2025-01-01", "end_date": "2025-01-07"},
                },
                tool_name="get_historical_weather",
                tool_args={"latitude": 40.7, "longitude": -74.0, "start_date": "2025-01-01", "end_date": "2025-01-07"},
                user_name="test_user"
            )
            
            # Mock tool results
            mock_tool_result_1 = {
                "status": ActivityStatus.SUCCESS,
                "trajectory": {
                    "thought_0": "Need current weather",
                    "tool_name_0": "get_weather_forecast",
                    "tool_args_0": {"latitude": 40.7, "longitude": -74.0, "days": 1},
                    "observation_0": "Current: 20°C"
                }
            }
            
            mock_tool_result_2 = {
                "status": ActivityStatus.SUCCESS,
                "trajectory": {
                    "thought_0": "Need current weather",
                    "tool_name_0": "get_weather_forecast",
                    "tool_args_0": {"latitude": 40.7, "longitude": -74.0, "days": 1},
                    "observation_0": "Current: 20°C",
                    "thought_1": "Now need historical data",
                    "tool_name_1": "get_historical_weather",
                    "tool_args_1": {"latitude": 40.7, "longitude": -74.0, "start_date": "2025-01-01", "end_date": "2025-01-07"},
                    "observation_1": "Historical avg: 15°C"
                }
            }
            
            # Mock final extract
            mock_extract_result = ExtractAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                answer="Current temperature is 20°C, warmer than the historical average of 15°C.",
                trajectory=mock_tool_result_2["trajectory"]
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
                    return ReactAgentActivityResult(
                        status=ActivityStatus.SUCCESS,
                        trajectory=mock_tool_result_2["trajectory"],
                        tool_name="",  # Empty string instead of None
                        tool_args={},  # Empty dict instead of None
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
                # Start workflow
                handle = await env.client.start_workflow(
                    AgenticAIWorkflow.run,
                    {"user_query": "Compare current weather to last week", "user_name": "test_user"},
                    id="test-workflow-multiple-tools",
                    task_queue="test-task-queue",
                )
                
                # Get result
                result = await handle.result()
                
                # Verify result is a Response object
                assert result.message
                assert "20°C" in result.message
                assert "15°C" in result.message
                assert result.query_count >= 1
                # The workflow reaches max iterations (5) so we expect 5 react calls
                assert react_call_count == 5  # Reaches max iterations
                assert tool_call_count == 5   # Tool executions match react calls