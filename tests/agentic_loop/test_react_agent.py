"""Tests for React agent with consolidated MCP tools."""
import pytest

from agentic_loop.react_agent import ReactAgent
from shared.tool_utils.agriculture_tool_set import AgricultureToolSet
from shared.tool_utils.registry import create_tool_set_registry


class TestReactAgentMCP:
    """Tests for React agent with consolidated MCP tools."""
    
    def test_react_agent_has_consolidated_tools(self):
        """Test that React agent has access to consolidated MCP tools."""
        # Create registry with agriculture tools
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Create React agent
        signature = registry.get_react_signature()
        agent = ReactAgent(signature=signature, tool_registry=registry)
        
        # Verify agent has access to all tools
        available_tools = agent.tool_registry.get_tool_names()
        
        # Should have 3 tools total (consolidated)
        assert len(available_tools) == 3
        
        # Only consolidated tools should be available
        assert "get_weather_forecast" in available_tools
        assert "get_historical_weather" in available_tools
        assert "get_agricultural_conditions" in available_tools
        
        # No _mcp suffix tools
        assert "get_weather_forecast_mcp" not in available_tools
        assert "get_historical_weather_mcp" not in available_tools
        assert "get_agricultural_conditions_mcp" not in available_tools
    
    def test_consolidated_tools_are_mcp_enabled(self):
        """Test that consolidated tools are properly configured as MCP tools."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Get tools
        forecast_tool = registry.get_tool("get_weather_forecast")
        historical_tool = registry.get_tool("get_historical_weather")
        agricultural_tool = registry.get_tool("get_agricultural_conditions")
        
        # All tools should have is_mcp = True
        assert forecast_tool.__class__.is_mcp is True
        assert historical_tool.__class__.is_mcp is True
        assert agricultural_tool.__class__.is_mcp is True
        
        # Tools should have MCP configuration
        assert hasattr(forecast_tool, 'mcp_server_name')
        # Note: mcp_tool_name has been removed - tool names are now computed dynamically
        assert hasattr(forecast_tool, 'get_mcp_config')
    
    def test_tool_descriptions_mention_weather(self):
        """Test that tool descriptions are appropriate."""
        registry = create_tool_set_registry("agriculture", mock_results=True)
        
        # Get tools
        forecast_tool = registry.get_tool("get_weather_forecast")
        historical_tool = registry.get_tool("get_historical_weather")
        agricultural_tool = registry.get_tool("get_agricultural_conditions")
        
        # Check descriptions
        assert "forecast" in forecast_tool.description.lower()
        assert "historical" in historical_tool.description.lower()
        assert "agricultural" in agricultural_tool.description.lower()