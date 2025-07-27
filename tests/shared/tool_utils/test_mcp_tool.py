"""Tests for MCPTool base class."""
from typing import ClassVar, Type
from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field

from models.types import MCPConfig
from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool


class SampleArguments(BaseModel):
    """Test arguments model."""
    message: str = Field(description="Test message")
    count: int = Field(default=1, description="Number of times")


class SampleMCPTool(MCPTool):
    """Test MCP tool implementation."""
    
    NAME: ClassVar[str] = "test_mcp_tool"
    MODULE: ClassVar[str] = "test.tools.test_mcp"
    
    description: str = "Test MCP tool"
    args_model: Type[BaseModel] = SampleArguments


class TestMCPToolClass:
    """Tests for MCPTool functionality."""
    
    def test_mcp_tool_creation(self):
        """Test that MCP tools can be created with required fields."""
        tool = SampleMCPTool()
        
        assert tool.NAME == "test_mcp_tool"
        assert tool.MODULE == "test.tools.test_mcp"
        assert tool.description == "Test MCP tool"
        assert tool.__class__.is_mcp is True  # Check class variable
        # No mcp_server_name field - all tools use single server
    
    def test_get_mcp_config_default(self):
        """Test get_mcp_config returns correct configuration with default settings."""
        tool = SampleMCPTool()
        config = tool.get_mcp_config()
        
        assert isinstance(config, MCPConfig)
        assert config.server_name == "weather-mcp"
        assert config.tool_name == "test_mcp_tool"  # Always unprefixed
        assert config.server_definition.name == "weather-mcp"
        assert config.server_definition.connection_type == "http"
        assert config.server_definition.url == "http://localhost:7778/mcp"
    
    @patch.dict("os.environ", {"MCP_SERVER_URL": "http://custom-server:9999/mcp"})
    def test_get_mcp_config_custom_url(self):
        """Test get_mcp_config uses custom MCP_SERVER_URL from environment."""
        tool = SampleMCPTool()
        config = tool.get_mcp_config()
        
        assert isinstance(config, MCPConfig)
        assert config.server_name == "weather-mcp"
        assert config.tool_name == "test_mcp_tool"  # Always unprefixed
        assert config.server_definition.name == "weather-mcp"
        assert config.server_definition.connection_type == "http"
        assert config.server_definition.url == "http://custom-server:9999/mcp"
    
    def test_execute_raises_error(self):
        """Test that execute method raises RuntimeError for MCP tools."""
        tool = SampleMCPTool()
        
        with pytest.raises(RuntimeError) as exc_info:
            tool.execute(message="test", count=5)
        
        assert "test_mcp_tool" in str(exc_info.value)
        assert "should be executed via activity" in str(exc_info.value)
    
    def test_arguments_extracted_from_model(self):
        """Test that arguments are properly extracted from args_model."""
        tool = SampleMCPTool()
        
        args = tool.get_argument_list()
        assert "message" in args
        assert "count" in args
        
        details = tool.get_argument_details()
        message_arg = next(d for d in details if d["name"] == "message")
        count_arg = next(d for d in details if d["name"] == "count")
        
        assert message_arg["required"] is True
        assert message_arg["description"] == "Test message"
        
        assert count_arg["required"] is False
        assert count_arg["default"] == 1
        assert count_arg["description"] == "Number of times"
    
    def test_validate_and_execute_raises_error(self):
        """Test that validate_and_execute also raises RuntimeError."""
        tool = SampleMCPTool()
        
        with pytest.raises(RuntimeError) as exc_info:
            tool.validate_and_execute(message="test", count=3)
        
        assert "test_mcp_tool" in str(exc_info.value)
        assert "should be executed via activity" in str(exc_info.value)
    
    def test_is_mcp_class_variable(self):
        """Test that is_mcp is properly set as a class variable."""
        # Check the class itself
        assert SampleMCPTool.is_mcp is True
        
        # Check instance access
        tool = SampleMCPTool()
        assert tool.__class__.is_mcp is True
        
        # Verify it's not an instance attribute
        assert 'is_mcp' not in tool.__dict__