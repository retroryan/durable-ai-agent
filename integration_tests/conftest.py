"""Pytest configuration and fixtures for integration tests."""
import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio

# Load environment variables
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add integration_tests directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import DurableAgentAPIClient

# Remove custom event_loop fixture - let pytest-asyncio handle it
# The session-scoped fixture was causing conflicts with pytest-asyncio


@pytest_asyncio.fixture
async def api_client() -> AsyncGenerator[DurableAgentAPIClient, None]:
    """
    Create an API client for the test session.

    This assumes the API server is already running.
    """
    # Get API URL from environment or use default
    api_url = os.getenv("API_URL", "http://localhost:8000")

    client = DurableAgentAPIClient(base_url=api_url)

    # Check if server is available
    try:
        await client.health_check()
    except Exception as e:
        pytest.skip(f"API server not available at {api_url}: {e}")

    yield client

    await client.close()


@pytest_asyncio.fixture
async def fresh_workflow_id() -> str:
    """Generate a fresh workflow ID for testing."""
    import uuid

    return f"test-workflow-{uuid.uuid4()}"


@pytest.fixture
def test_config() -> dict:
    """
    Test configuration settings.

    Returns:
        Configuration dictionary
    """
    return {
        "timeout": 30,
        "poll_interval": 0.5,
        "api_url": os.getenv("API_URL", "http://localhost:8000"),
    }


@pytest.fixture
def skip_if_no_api(api_client):
    """Skip test if API is not available."""
    # This fixture depends on api_client, which already checks availability
    pass


# Custom markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "api: marks tests that require the API server to be running"
    )
    config.addinivalue_line(
        "markers", "workflow: marks tests that test workflow functionality"
    )
    config.addinivalue_line("markers", "slow: marks tests that take longer to run")
