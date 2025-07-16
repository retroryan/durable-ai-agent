#!/bin/bash
set -e

echo "Running unit tests..."
poetry run pytest tests/unit -v

echo "Running integration tests..."
poetry run pytest tests/integration -v

echo "Starting docker-compose for E2E tests..."
docker-compose up -d

echo "Waiting for services..."
sleep 15

echo "Running E2E tests..."
TOOLS_MOCK=true poetry run pytest tests/e2e -v

echo "Cleaning up..."
docker-compose down

echo "All tests passed!"