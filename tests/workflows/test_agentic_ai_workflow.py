"""Tests for agentic AI workflow with MCP routing."""
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from activities.extract_agent_activity import ExtractAgentActivity
from activities.mcp_execution_activity import MCPExecutionActivity  
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
    """Tests for agentic AI workflow MCP routing."""
    
    async def test_workflow_routes_mcp_tools_correctly(self):
        """Test that workflow routes MCP tools to MCPExecutionActivity."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Mock activities
            mock_react_result = ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectory={
                    "thought_0": "I need to get weather forecast",
                    "tool_name_0": "weather_forecast_mcp",
                    "tool_args_0": {"location": "NYC", "days": 3},
                },
                tool_name="weather_forecast_mcp",
                tool_args={"location": "NYC", "days": 3},
                user_name="test_user"
            )
            
            # Mock tool execution result
            mock_tool_result = {
                "status": ActivityStatus.SUCCESS,
                "trajectory": {
                    "thought_0": "I need to get weather forecast",
                    "tool_name_0": "weather_forecast_mcp", 
                    "tool_args_0": {"location": "NYC", "days": 3},
                    "observation_0": "Weather forecast: Sunny for 3 days"
                }
            }
            
            # Mock extract result
            mock_extract_result = ExtractAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                answer="The weather forecast for NYC shows sunny conditions for the next 3 days.",
                reasoning="Based on the weather data retrieved",
                trajectory=mock_tool_result["trajectory"]
            )
            
            # Create mocked activities with proper decorators
            call_count = {"react": 0}
            
            @activity.defn(name="run_react_agent")
            async def mock_react_agent(*args):
                # Second call returns finish
                call_count["react"] += 1
                if call_count["react"] > 1:
                    return ReactAgentActivityResult(
                        status=ActivityStatus.SUCCESS,
                        trajectory=mock_tool_result["trajectory"],
                        tool_name="finish",
                        tool_args={},
                        user_name="test_user"
                    )
                return mock_react_result
            
            @activity.defn(name="execute_tool")
            async def mock_execute_tool(*args):
                return {"status": ActivityStatus.ERROR, "error": "Should not be called for MCP tools"}
            
            @activity.defn(name="execute_mcp_tool")
            async def mock_execute_mcp_tool(*args):
                return mock_tool_result
            
            @activity.defn(name="run_extract_agent")
            async def mock_extract_agent(*args):
                return mock_extract_result
            
            # Create worker with mocked activities
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[AgenticAIWorkflow],
                activities=[
                    mock_react_agent,
                    mock_execute_tool,
                    mock_execute_mcp_tool,
                    mock_extract_agent,
                ],
            ):
                # Execute workflow
                handle = await env.client.start_workflow(
                    AgenticAIWorkflow.run,
                    args=["weather: what's the forecast for NYC?", "test_user"],
                    id="test-mcp-routing",
                    task_queue="test-queue",
                )
                
                result = await handle.result()
                
                # Verify result
                assert "sunny" in result.message.lower()
                assert result.event_count == 1  # One tool was used
                assert result.query_count == 1
    
    async def test_workflow_routes_regular_tools_correctly(self):
        """Test that workflow routes non-MCP tools to ToolExecutionActivity."""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            # Mock activities
            mock_react_result = ReactAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                trajectory={
                    "thought_0": "I need to find events",
                    "tool_name_0": "find_events",
                    "tool_args_0": {"query": "concerts"},
                },
                tool_name="find_events",
                tool_args={"query": "concerts"},
                user_name="test_user"
            )
            
            # Mock tool execution result
            mock_tool_result = {
                "status": ActivityStatus.SUCCESS,
                "trajectory": {
                    "thought_0": "I need to find events",
                    "tool_name_0": "find_events",
                    "tool_args_0": {"query": "concerts"},
                    "observation_0": "Found 5 concerts this week"
                }
            }
            
            # Mock extract result
            mock_extract_result = ExtractAgentActivityResult(
                status=ActivityStatus.SUCCESS,
                answer="I found 5 concerts happening this week.",
                reasoning="Based on event search results",
                trajectory=mock_tool_result["trajectory"]
            )
            
            # Create mocked activities with proper decorators
            call_count = {"react": 0}
            
            @activity.defn(name="run_react_agent")
            async def mock_react_agent(*args):
                # Second call returns finish
                call_count["react"] += 1
                if call_count["react"] > 1:
                    return ReactAgentActivityResult(
                        status=ActivityStatus.SUCCESS,
                        trajectory=mock_tool_result["trajectory"],
                        tool_name="finish",
                        tool_args={},
                        user_name="test_user"
                    )
                return mock_react_result
            
            @activity.defn(name="execute_tool")
            async def mock_execute_tool(*args):
                return mock_tool_result
            
            @activity.defn(name="execute_mcp_tool")
            async def mock_execute_mcp_tool(*args):
                return {"status": ActivityStatus.ERROR, "error": "Should not be called for regular tools"}
            
            @activity.defn(name="run_extract_agent")
            async def mock_extract_agent(*args):
                return mock_extract_result
            
            # Create worker with mocked activities
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[AgenticAIWorkflow],
                activities=[
                    mock_react_agent,
                    mock_execute_tool,
                    mock_execute_mcp_tool,
                    mock_extract_agent,
                ],
            ):
                # Execute workflow
                handle = await env.client.start_workflow(
                    AgenticAIWorkflow.run,
                    args=["find concerts near me", "test_user"],
                    id="test-regular-routing",
                    task_queue="test-queue",
                )
                
                result = await handle.result()
                
                # Verify result
                assert "5 concerts" in result.message
                assert result.event_count == 1  # One tool was used
                assert result.query_count == 1