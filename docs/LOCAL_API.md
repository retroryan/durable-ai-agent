# Running API Server Locally

This guide explains how to run the API server locally while keeping Temporal services in Docker Compose.

## Overview

The docker-compose.yml uses profiles to control which services start. The API server has the profile `api_server`, which means it won't start by default when running `docker-compose up`.

## Setup Steps

### 1. Start Temporal Services Only

Start Temporal and the worker without the API server:

```bash
# Start core services (Temporal, PostgreSQL, worker, UI)
docker-compose up

# Or explicitly exclude the api_server profile
docker-compose up --profile ""
```

This will start:
- PostgreSQL database
- Temporal server (port 7233)
- Temporal UI (port 8080)
- Worker service

### 2. Configure Local API Environment

The `.env` file contains all the necessary configuration. When running locally, the script will override `TEMPORAL_ADDRESS` to use `localhost:7233` instead of the Docker service name.

### 3. Run API Server Locally

Use the provided script to run the API server:

```bash
./scripts/run_api_local.sh
```

This script will:
- Load environment variables from `.env`
- Override `TEMPORAL_ADDRESS` to `localhost:7233` for local development
- Start the API server on port 8000
- Start the frontend development server on port 3000
- Enable hot reload for development

### Alternative: Manual Run

You can also run the API server manually:

```bash
# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Override for local development
export TEMPORAL_ADDRESS=localhost:7233

# Run with poetry
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Available Services

With this setup, you'll have:
- **API Server**: http://localhost:8000 (running locally)
- **API Docs**: http://localhost:8000/docs
- **Temporal UI**: http://localhost:8080
- **Temporal Server**: localhost:7233

## Benefits of Local API Development

- Hot reload for faster development
- Easy debugging with local IDE
- Direct access to logs and console output
- Ability to set breakpoints
- No need to rebuild Docker image for API changes

## Troubleshooting

1. **Connection refused to Temporal**: Ensure Docker services are running
2. **Port already in use**: Check if another process is using port 8000
3. **Module not found**: Run `poetry install` to ensure dependencies are installed

## Including API in Docker

If you want to run the API server in Docker instead:

```bash
docker-compose --profile api_server up
```

This will start all services including the API server in a container.