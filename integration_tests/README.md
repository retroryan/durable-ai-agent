# Integration Tests

This directory contains integration tests that test the durable AI agent API by making actual HTTP requests to a running server.

## Prerequisites

1. The API server must be running before running these tests
2. Temporal must be running
3. The worker must be running

## Setup

1. Start the services (from the project root):
   ```bash
   docker-compose up
   ```

2. Or run services locally:
   ```bash
   # Terminal 1: Start Temporal
   temporal server start-dev
   
   # Terminal 2: Start the worker
   poetry run python worker/main.py
   
   # Terminal 3: Start the API
   poetry run python -m api.main
   ```

## Running Tests

From the project root:

```bash
# Run all integration tests
poetry run pytest integration_tests/ -v

# Run only API endpoint tests
poetry run pytest integration_tests/test_api_endpoints.py -v

# Run only workflow tests
poetry run pytest integration_tests/test_workflow_integration.py -v

# Run tests with specific markers
poetry run pytest integration_tests/ -m api -v
poetry run pytest integration_tests/ -m workflow -v

# Run with custom API URL
API_URL=http://localhost:8001 poetry run pytest integration_tests/ -v
```

## Test Structure

- `conftest.py` - Pytest configuration and fixtures
- `utils/` - Test utilities
  - `api_client.py` - HTTP client wrapper for API calls
  - `test_helpers.py` - Assertion helpers and utilities
- `test_api_endpoints.py` - Tests for API endpoints
- `test_workflow_integration.py` - Tests for workflow functionality

## Test Categories

Tests are marked with the following markers:
- `@pytest.mark.api` - Tests that require the API server
- `@pytest.mark.workflow` - Tests for workflow functionality
- `@pytest.mark.slow` - Tests that take longer to run

## Writing New Tests

1. Use the `api_client` fixture to make API calls
2. Use `WorkflowAssertions` for common assertions
3. Mark tests appropriately with `@pytest.mark.api` or `@pytest.mark.workflow`
4. Use `async def` for all test functions

Example:
```python
@pytest.mark.api
@pytest.mark.asyncio
async def test_my_feature(api_client):
    response = await api_client.chat("Test message")
    WorkflowAssertions.assert_workflow_completed(response)
```

## Debugging

If tests fail with connection errors:
1. Check that all services are running
2. Check the API_URL environment variable
3. Check service logs for errors
4. Verify Temporal UI at http://localhost:8080