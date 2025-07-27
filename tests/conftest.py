"""Test configuration and fixtures."""
import os
import pytest


@pytest.fixture(autouse=True)
def clean_mcp_env():
    """Remove MCP_SERVER_URL from environment for tests to use default localhost."""
    # Store original value if exists
    original_value = os.environ.get("MCP_SERVER_URL")
    
    # Remove it for the test
    if "MCP_SERVER_URL" in os.environ:
        del os.environ["MCP_SERVER_URL"]
    
    yield
    
    # Restore original value if it existed
    if original_value is not None:
        os.environ["MCP_SERVER_URL"] = original_value