"""Tests for MCPTool base class."""
from typing import Type

import pytest
from pydantic import BaseModel, Field

from models.tool_definitions import MCPServerDefinition
from shared.tool_utils.mcp_tool import MCPTool


class TestArguments(BaseModel):
    """Test arguments model."""
    message: str = Field(description="Test message")
    count: int = Field(default=1, description="Number of times")


class TestMCPTool(MCPTool):
    """Test MCP tool implementation."""
    
    NAME = "test_mcp_tool"
    MODULE = "test.tools.test_mcp"
    
    description: str = "Test MCP tool"
    args_model: Type[BaseModel] = TestArguments
    
    mcp_server_name: str = "test_server"
    mcp_tool_name: str = "test_tool"
    mcp_server_definition: MCPServerDefinition = MCPServerDefinition(
        name="test-server",
        connection_type="http",
        url="http://localhost:8000/mcp"
    )


class TestMCPToolClass:
    """Tests for MCPTool functionality."""
    
    def test_mcp_tool_creation(self):
        """Test that MCP tools can be created with required fields."""
        tool = TestMCPTool()
        
        assert tool.NAME == "test_mcp_tool"
        assert tool.MODULE == "test.tools.test_mcp"
        assert tool.description == "Test MCP tool"
        assert tool.uses_mcp is True
        assert tool.mcp_server_name == "test_server"
        assert tool.mcp_tool_name == "test_tool"
        assert tool.mcp_server_definition.name == "test-server"
        assert tool.mcp_server_definition.connection_type == "http"
        assert tool.mcp_server_definition.url == "http://localhost:8000/mcp"
    
    def test_get_mcp_config(self):
        """Test get_mcp_config returns correct configuration."""
        tool = TestMCPTool()
        config = tool.get_mcp_config()
        
        assert config["server_name"] == "test_server"
        assert config["tool_name"] == "test_tool"
        assert config["server_definition"].name == "test-server"
        assert config["server_definition"].connection_type == "http"
        assert config["server_definition"].url == "http://localhost:8000/mcp"
    
    def test_execute_raises_error(self):
        """Test that execute method raises RuntimeError for MCP tools."""
        tool = TestMCPTool()
        
        with pytest.raises(RuntimeError) as exc_info:
            tool.execute(message="test", count=5)
        
        assert "test_mcp_tool" in str(exc_info.value)
        assert "MCPExecutionActivity" in str(exc_info.value)
    
    def test_arguments_extracted_from_model(self):
        """Test that arguments are properly extracted from args_model."""
        tool = TestMCPTool()
        
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
        tool = TestMCPTool()
        
        with pytest.raises(RuntimeError) as exc_info:
            tool.validate_and_execute(message="test", count=3)
        
        assert "test_mcp_tool" in str(exc_info.value)
        assert "MCPExecutionActivity" in str(exc_info.value)