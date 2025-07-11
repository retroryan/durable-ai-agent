# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based distributed workflow application demonstrating durable AI conversation patterns using Temporal. The project uses FastAPI for the API server, Temporal for workflow orchestration, and Docker Compose for containerized deployment.

**IMPORTANT: This is a DEMO project designed for simplicity and clarity.** The goal is to maintain a clean, modular, and easy-to-understand codebase that demonstrates core concepts. This is NOT a complex production implementation. When making changes:
- Prioritize simplicity and readability over complex optimizations
- Keep components modular and loosely coupled
- Avoid over-engineering or adding unnecessary complexity
- Focus on demonstrating the core Temporal workflow patterns clearly

## Essential Commands

### Development Setup
```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
```

### Code Quality
```bash
poetry run poe format     # Format code with black and isort
poetry run poe lint       # Run all linters (black, isort, mypy)
poetry run poe lint-types # Run type checking only
```

### Testing
```bash
# Unit tests (no services required)
poetry run poe test

# Integration tests (requires docker-compose up)
docker-compose up -d
poetry run pytest integration_tests/ -v

# Test specific components
poetry run pytest integration_tests/ -m api -v
poetry run pytest integration_tests/ -m workflow -v
```

### Running the Application
```bash
# Start all services (recommended)
docker-compose up

# Access services at:
# - API: http://localhost:8000 (docs at /docs)
# - Temporal UI: http://localhost:8080
```

## Architecture Overview

The application follows a microservices architecture with these key components:

1. **API Server** (`api/`) - FastAPI application providing REST endpoints for workflow management
2. **Worker** (`worker/`) - Processes Temporal workflows and activities
3. **Workflows** (`workflows/`) - Durable workflow definitions (SimpleAgentWorkflow)
4. **Activities** (`activities/`) - Atomic units of work (find_events_activity)
5. **Tools** (`tools/`) - Reusable tool implementations (find_events)

### Key Design Patterns

- **Workflow Pattern**: Each conversation is a long-running Temporal workflow that maintains state
- **Message Processing**: Messages are processed through activities with automatic retry and error handling
- **Query Pattern**: Workflow state can be queried at any time without affecting execution
- **Signal Pattern**: New messages are sent to workflows via signals

### API Endpoints

- `POST /chat` - Start a new workflow with an initial message
- `GET /workflow/{workflow_id}/status` - Check workflow execution status
- `GET /workflow/{workflow_id}/query` - Query current workflow state

## Testing Strategy

- **Unit Tests** (`tests/`) - Test individual components in isolation
- **Integration Tests** (`integration_tests/`) - Test API endpoints with real Temporal backend
- Use markers (`-m api`, `-m workflow`) to run specific test categories
- Integration tests require services to be running via docker-compose

## Important Notes

- Always ensure docker-compose services are running before integration tests
- The project uses Poetry for dependency management - avoid pip install
- Type hints are enforced - run `poetry run poe lint-types` before committing
- Frontend components (Phase 4) are not yet implemented

## Code Quality Requirements

**ALWAYS run linting checks after implementing code changes:**
```bash
poetry run poe lint
```

If linting fails, fix the issues by:
1. Running `poetry run poe format` to auto-fix formatting issues
2. Addressing any type errors reported by mypy
3. Running `poetry run poe lint` again to verify all checks pass

This ensures the codebase maintains high quality standards and type safety.