# Durable AI Agent

A simplified demonstration of durable AI conversations using Temporal workflows. This project shows how to build reliable, persistent workflows without complex AI logic.

## Overview

This project is a minimal implementation that:
- Demonstrates Temporal workflow patterns
- Shows activity execution with retry logic
- Maintains state across workflow restarts
- Provides a clean foundation for extension

## Architecture

The system consists of:
- **Workflow**: Simple workflow that tracks query count and executes activities
- **Activity**: Calls a hardcoded tool (find_events) with fixed parameters
- **API**: FastAPI server for workflow management
- **Frontend**: React UI for chat interaction

## Current Status

✅ **Phase 1**: Infrastructure setup complete
✅ **Phase 2**: Core backend components complete
✅ **Phase 3**: API server complete
✅ **Phase 4**: Frontend UI complete
⬜ **Phase 5**: Integration testing (not started)
⬜ **Phase 6**: MCP integration (not started)

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)

### Running the Complete System

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd durable-ai-agent
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   ```

3. **Start all services with Docker Compose**
   ```bash
   docker-compose up
   ```

4. **Access the applications**
   - 🌐 **Frontend (Chat UI)**: http://localhost:3000
   - 📡 **API Server**: http://localhost:8000
   - 📚 **API Documentation**: http://localhost:8000/docs
   - ⚙️ **Temporal UI**: http://localhost:8080

### What Gets Started

Docker Compose will start the following services:
- **PostgreSQL**: Database for Temporal
- **Temporal Server**: Workflow orchestration engine
- **Temporal UI**: Web interface for monitoring workflows
- **API Server**: FastAPI backend at port 8000
- **Worker**: Processes Temporal workflows and activities
- **Frontend**: React chat interface at port 3000

### Using the Chat Interface

1. Open http://localhost:3000 in your browser
2. Type a message in the input field
3. The system will:
   - Create a new Temporal workflow
   - Execute the find_events activity
   - Return information about events in Melbourne
4. The workflow ID and status are displayed in the header
5. Click "New Conversation" to start a fresh workflow

### Development Mode

For local development without Docker:

```bash
# Terminal 1: Start Temporal (requires Temporal CLI)
temporal server start-dev

# Terminal 2: Start the worker
poetry install
poetry run python worker/main.py

# Terminal 3: Start the API server
poetry run python api/main.py

# Terminal 4: Start the frontend
cd frontend
npm install
npm run dev
```

## Running Tests

### Prerequisites
1. Install Poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Create .env file: `cp .env.example .env`

### Unit Tests
```bash
# Run unit tests
poetry run pytest tests/

# Run with verbose output
poetry run pytest tests/ -v
```

### Integration Tests (API Server Tests)
Integration tests require the full stack to be running:

```bash
# Start services (in separate terminals or use docker-compose)
docker-compose up

# Run integration tests
poetry run pytest integration_tests/ -v

# Run specific test categories
poetry run pytest integration_tests/ -m api -v
poetry run pytest integration_tests/ -m workflow -v
```

### Test Coverage

**Unit Tests** (`tests/`):
- ✅ Basic workflow execution
- ✅ Query count functionality  
- ✅ Workflow ID handling
- ✅ Activity execution

**Integration Tests** (`integration_tests/`):
- ✅ API endpoint testing
- ✅ Workflow creation and execution via API
- ✅ Concurrent workflow handling
- ✅ Error handling and validation
- ✅ Query and status endpoints

All tests are passing! The project successfully demonstrates:
- Temporal workflow patterns with proper state management
- Activity execution with retry policies
- Query handlers for workflow introspection
- Integration with external tools (find_events)
- Full API integration testing

## API Endpoints

- `POST /chat` - Start a workflow with a message
- `GET /workflow/{workflow_id}/status` - Get workflow status
- `GET /workflow/{workflow_id}/query` - Query workflow state
- `GET /health` - Health check
- `GET /docs` - API documentation

## Project Structure

```
durable-ai-agent/
├── workflows/          # Temporal workflows
├── activities/         # Temporal activities  
├── tools/             # Tool implementations
├── models/            # Data models
├── shared/            # Shared utilities
├── worker/            # Worker process
├── api/               # API server
├── frontend/          # React UI
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   └── services/     # API client
│   └── Dockerfile        # Frontend container
├── docker-compose.yml  # Service orchestration
└── tests/             # Test suites
```

## Key Simplifications

- No AI/LLM integration
- Single hardcoded tool execution
- Fixed parameters (Melbourne, current month)
- Minimal state management
- No complex routing or planning

## Temporal Best Practices

### Key Points from Temporal Documentation

- **Activity IDs** are only unique within a workflow run, not globally
- **Task Tokens** provide unique identification for activity executions
- **Workflow IDs** are unique within a namespace and commonly include business identifiers
- **User Context**: Always pass user-specific data explicitly as parameters rather than relying on implicit context
- **Activity Context**: Activities have access to workflow ID, activity ID, task queue, and attempt number through `activity.info()`

## Next Steps

See `durable-ai-agent.md` for the complete implementation plan and architecture guide.

## Integration Tests Details

The project includes comprehensive integration tests that test the API server with actual HTTP requests.

### Integration Test Structure

```
integration_tests/
├── README.md              # Integration test documentation
├── conftest.py            # Pytest configuration and fixtures
├── utils/                 # Test utilities
│   ├── api_client.py      # HTTP client wrapper for API calls
│   └── test_helpers.py    # Assertion helpers and utilities
├── test_api_endpoints.py  # Tests for API endpoints
└── test_workflow_integration.py  # Tests for workflow functionality
```

### Test Utilities

**DurableAgentAPIClient** (`utils/api_client.py`):
- Async HTTP client using `httpx`
- Methods for all API endpoints: `chat()`, `get_workflow_status()`, `query_workflow()`
- Helper methods like `wait_for_workflow_completion()`
- Configurable timeout and base URL

**WorkflowAssertions** (`utils/test_helpers.py`):
- `assert_workflow_started()` - Verifies workflow creation
- `assert_workflow_completed()` - Checks completion status
- `assert_events_found()` - Validates event finder results
- `get_workflow_id()`, `get_event_count()`, `get_query_count()` - Extract data from responses

### Test Coverage

**API Endpoint Tests**:
- ✅ Health check endpoint (`/health`)
- ✅ Root endpoint (`/`)
- ✅ Chat endpoint (`/chat`) - workflow creation
- ✅ Workflow status (`/workflow/{id}/status`)
- ✅ Workflow query (`/workflow/{id}/query`)
- ✅ Error handling (404, 422 responses)

**Workflow Integration Tests**:
- ✅ Activity execution verification
- ✅ Query count state persistence
- ✅ Multiple workflow isolation
- ✅ Custom workflow ID support
- ✅ Concurrent workflow execution
- ✅ Response format validation

### Running Integration Tests

```bash
# Prerequisites: Start all services
docker-compose up

# Run all integration tests
poetry run pytest integration_tests/ -v

# Run only API tests
poetry run pytest integration_tests/test_api_endpoints.py -v

# Run only workflow tests
poetry run pytest integration_tests/test_workflow_integration.py -v

# Run by marker
poetry run pytest integration_tests/ -m api -v
poetry run pytest integration_tests/ -m workflow -v

# Run with custom API URL
API_URL=http://localhost:8001 poetry run pytest integration_tests/ -v
```

### Key Features

- **Async Testing**: All tests use `pytest-asyncio` for async/await support
- **Fixtures**: Session-scoped API client, fresh workflow IDs, test configuration
- **Markers**: Tests are marked with `@pytest.mark.api` or `@pytest.mark.workflow`
- **Real HTTP Calls**: Tests make actual HTTP requests to the running API server
- **Comprehensive Assertions**: Helper functions for common workflow validations
- **Error Handling**: Tests verify both success and error scenarios

### Writing New Integration Tests

Example of adding a new integration test:

```python
@pytest.mark.api
@pytest.mark.asyncio
async def test_my_feature(api_client):
    # Make API call
    response = await api_client.chat("Test message")
    
    # Use assertion helpers
    WorkflowAssertions.assert_workflow_completed(response)
    assert "Melbourne" in response["last_response"]["message"]
```

The integration tests ensure the entire system works correctly end-to-end, complementing the unit tests that test individual components in isolation.