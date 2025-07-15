"""Tests for React agent with MCP tools."""
import pytest

from agentic_loop.react_agent import ReactAgent
from shared.tool_utils.agriculture_tool_set import AgricultureToolSet
from shared.tool_utils.registry import create_tool_set_registry


class TestReactAgentMCP:
    """Tests for React agent selecting MCP tools."""
    
    def test_react_agent_can_see_mcp_tools(self):
        """Test that React agent has access to both traditional and MCP tools."""
        # Create registry with agriculture tools
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Create React agent
        signature = registry.get_react_signature()
        agent = ReactAgent(signature=signature, tool_registry=registry)
        
        # Verify agent has access to all tools
        available_tools = agent.tool_registry.get_tool_names()
        
        # Should have 6 tools total
        assert len(available_tools) == 6
        
        # Both types should be available
        assert "get_weather_forecast" in available_tools
        assert "get_weather_forecast_mcp" in available_tools
        assert "get_historical_weather" in available_tools
        assert "get_historical_weather_mcp" in available_tools
        assert "get_agricultural_conditions" in available_tools
        assert "get_agricultural_conditions_mcp" in available_tools
    
    def test_react_agent_tool_descriptions_differ(self):
        """Test that MCP tools have different descriptions to help agent selection."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        agent = ReactAgent(signature=registry.get_react_signature(), tool_registry=registry)
        
        # Get tool descriptions
        traditional_forecast = registry.get_tool("get_weather_forecast")
        mcp_forecast = registry.get_tool("get_weather_forecast_mcp")
        
        # Descriptions should be different
        assert traditional_forecast.description != mcp_forecast.description
        
        # MCP tool should mention MCP in description
        assert "mcp" not in traditional_forecast.description.lower()
        assert "mcp" in mcp_forecast.description.lower()
        
        # Both should mention weather forecast
        assert "weather forecast" in traditional_forecast.description.lower()
        assert "weather forecast" in mcp_forecast.description.lower()