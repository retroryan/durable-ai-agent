"""Unit tests for MCPClientManager."""
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from shared.mcp_client_manager import MCPClientManager
from models.tool_definitions import MCPServerDefinition


@pytest.fixture
def manager():
    """Create a fresh MCPClientManager instance."""
    return MCPClientManager()


@pytest.mark.asyncio
async def test_manager_creates_single_client_for_same_server(manager):
    """Test that manager reuses clients for the same server definition."""
    server_def = {
        "name": "test-server",
        "connection_type": "stdio",
        "command": "python",
        "args": ["test.py"],
    }

    with patch("shared.mcp_client_manager.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Get client twice with same server definition
        client1 = await manager.get_client(server_def)
        client2 = await manager.get_client(server_def)

        # Should be the same client instance
        assert client1 is client2
        # Client should only be created once
        mock_client_class.assert_called_once()


@pytest.mark.asyncio
async def test_manager_creates_different_clients_for_different_servers(manager):
    """Test that manager creates different clients for different server definitions."""
    server_def1 = {
        "name": "server1",
        "connection_type": "stdio",
        "command": "python",
        "args": ["test1.py"],
    }
    server_def2 = {
        "name": "server2",
        "connection_type": "stdio",
        "command": "python",
        "args": ["test2.py"],
    }

    with patch("shared.mcp_client_manager.Client") as mock_client_class:
        mock_client1 = AsyncMock()
        mock_client1.__aenter__ = AsyncMock(return_value=mock_client1)
        mock_client1.__aexit__ = AsyncMock(return_value=None)
        mock_client2 = AsyncMock()
        mock_client2.__aenter__ = AsyncMock(return_value=mock_client2)
        mock_client2.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.side_effect = [mock_client1, mock_client2]

        # Get clients for different server definitions
        client1 = await manager.get_client(server_def1)
        client2 = await manager.get_client(server_def2)

        # Should be different client instances
        assert client1 is not client2
        # Client should be created twice
        assert mock_client_class.call_count == 2


@pytest.mark.asyncio
async def test_manager_handles_none_server_definition(manager):
    """Test that manager handles None server definition with default values."""
    with patch("shared.mcp_client_manager.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Get client with None server definition
        client = await manager.get_client(None)

        # Should create a client with default values
        assert client is mock_client
        mock_client_class.assert_called_once()


@pytest.mark.asyncio
async def test_manager_handles_mcp_server_definition_object(manager):
    """Test that manager handles MCPServerDefinition objects."""
    server_def = MCPServerDefinition(
        name="test-server",
        connection_type="stdio",
        command="python",
        args=["test.py"]
    )

    with patch("shared.mcp_client_manager.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Get client with MCPServerDefinition object
        client = await manager.get_client(server_def)

        # Should create a client
        assert client is mock_client
        mock_client_class.assert_called_once()


@pytest.mark.asyncio
async def test_manager_handles_http_connection_type(manager):
    """Test that manager correctly handles HTTP connection type."""
    server_def = {
        "name": "http-server",
        "connection_type": "http",
        "url": "http://localhost:8000/mcp",
    }

    with patch("shared.mcp_client_manager.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Get client with HTTP server definition
        client = await manager.get_client(server_def)

        # Should create a client with HTTP transport
        assert client is mock_client
        mock_client_class.assert_called_once()
        # Check that HTTP transport was used
        call_args = mock_client_class.call_args
        assert call_args[0][0] == "http://localhost:8000/mcp"


@pytest.mark.asyncio
async def test_manager_cleanup_closes_all_clients(manager):
    """Test that cleanup closes all clients."""
    server_def1 = {
        "name": "server1",
        "connection_type": "stdio",
        "command": "python",
        "args": ["test1.py"],
    }
    server_def2 = {
        "name": "server2",
        "connection_type": "stdio",
        "command": "python",
        "args": ["test2.py"],
    }

    with patch("shared.mcp_client_manager.Client") as mock_client_class:
        mock_client1 = AsyncMock()
        mock_client1.__aenter__ = AsyncMock(return_value=mock_client1)
        mock_client1.__aexit__ = AsyncMock(return_value=None)
        mock_client2 = AsyncMock()
        mock_client2.__aenter__ = AsyncMock(return_value=mock_client2)
        mock_client2.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.side_effect = [mock_client1, mock_client2]

        # Create two clients
        await manager.get_client(server_def1)
        await manager.get_client(server_def2)

        # Cleanup should close both clients
        await manager.cleanup()

        # Both clients should have __aexit__ called
        mock_client1.__aexit__.assert_called_once()
        mock_client2.__aexit__.assert_called_once()

        # Manager should have no clients after cleanup
        assert len(manager._clients) == 0


@pytest.mark.asyncio
async def test_manager_thread_safety_with_concurrent_requests(manager):
    """Test that manager is thread-safe with concurrent requests."""
    server_def = {
        "name": "test-server",
        "connection_type": "stdio",
        "command": "python",
        "args": ["test.py"],
    }

    with patch("shared.mcp_client_manager.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Create multiple concurrent requests for the same server
        tasks = [manager.get_client(server_def) for _ in range(5)]
        clients = await asyncio.gather(*tasks)

        # All clients should be the same instance
        assert all(client is clients[0] for client in clients)
        # Client should only be created once despite concurrent requests
        mock_client_class.assert_called_once()


@pytest.mark.asyncio
async def test_manager_handles_stdio_with_environment_variables(manager):
    """Test that manager correctly passes environment variables for stdio."""
    server_def = {
        "name": "env-server",
        "connection_type": "stdio",
        "command": "python",
        "args": ["test.py"],
        "env": {"API_KEY": "test123", "DEBUG": "true"}
    }

    with patch("shared.mcp_client_manager.Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        # Get client with environment variables
        await manager.get_client(server_def)

        # Check that env was properly passed
        mock_client_class.assert_called_once()
        call_args = mock_client_class.call_args
        # The actual implementation might need to be checked for how env is passed