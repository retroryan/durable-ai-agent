import pytest
import asyncio
import subprocess
import time
import os
from temporalio.client import Client


@pytest.fixture(scope="session")
def docker_compose_up():
    """Start docker-compose services for testing"""
    # Check if services are already running
    result = subprocess.run(
        ["docker", "compose", "ps", "-q"],
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("Docker compose services already running")
        yield
        return
    
    # Start services
    print("Starting docker-compose services...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    
    # Wait for services to be ready
    print("Waiting for services to be ready...")
    time.sleep(15)  # Basic wait, could be improved with health checks
    
    yield
    
    # Note: Not tearing down automatically to allow inspection
    print("Docker compose services left running for inspection")


@pytest.fixture
async def temporal_client(docker_compose_up):
    """Create Temporal client connected to docker-compose services"""
    client = await Client.connect("localhost:7233")
    return client


@pytest.fixture
def ensure_mock_mode():
    """Ensure MCP servers are in mock mode for testing"""
    os.environ["TOOLS_MOCK"] = "true"
    yield
    # Reset after test
    if "TOOLS_MOCK" in os.environ:
        del os.environ["TOOLS_MOCK"]


# Mark all e2e tests to require docker-compose
def pytest_collection_modifyitems(config, items):
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(pytest.mark.requires_docker)