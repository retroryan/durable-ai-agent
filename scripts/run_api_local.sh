#!/bin/bash
set -e

# Script to run the API server locally with environment settings from .env

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Load environment variables from .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment from .env..."
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
else
    echo "Error: .env file not found in $PROJECT_ROOT"
    echo "Please create .env file with required configuration"
    echo "You can copy .env.example as a starting point: cp .env.example .env"
    exit 1
fi

# Override TEMPORAL_ADDRESS for local development
export TEMPORAL_ADDRESS="localhost:7233"
echo "Note: Overriding TEMPORAL_ADDRESS to localhost:7233 for local development"

# Change to project root
cd "$PROJECT_ROOT"

echo "Starting API server locally..."
echo "Temporal Address: $TEMPORAL_ADDRESS"
echo "Temporal Namespace: $TEMPORAL_NAMESPACE"

# Function to cleanup background processes on exit
cleanup() {
    echo "Stopping services..."
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start the frontend dev server in the background
echo "Starting frontend dev server..."
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"

# Give frontend a moment to start
sleep 2

# Run the API server (this will block)
echo "Starting API server..."
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

echo ""
echo "Services started:"
echo "  - API server: http://localhost:8000"
echo "  - API docs: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait