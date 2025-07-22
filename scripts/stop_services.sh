#!/bin/bash

# Stop the client (frontend)
echo "Stopping frontend client..."
if pgrep -f "npm.*dev" > /dev/null; then
    pkill -f "npm.*dev"
    echo "Frontend stopped"
else
    echo "Frontend not running"
fi

# Stop the API server
echo "Stopping API server..."
if pgrep -f "uvicorn api.main:app" > /dev/null; then
    pkill -f "uvicorn api.main:app"
    echo "API server stopped"
else
    echo "API server not running"
fi

echo "All services stopped"