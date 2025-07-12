#!/bin/bash
# Run and test the MCP Proxy

echo "🚀 Starting MCP Proxy and running tests..."
echo "==========================================="

# Function to cleanup on exit
cleanup() {
    echo -e "\n🧹 Cleaning up..."
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
    fi
}
trap cleanup EXIT

# Start the proxy server in background
echo "1. Starting MCP Proxy server..."
cd "$(dirname "$0")"
python -m mcp_proxy.main &
SERVER_PID=$!

# Wait for server to start
echo "   Waiting for server to start..."
sleep 3

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Server failed to start!"
    exit 1
fi

echo "✅ Server started (PID: $SERVER_PID)"

# Run the tests
echo -e "\n2. Running integration tests..."
python tests/test_mcp_proxy.py

# Capture test exit code
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "\n✅ All tests passed!"
else
    echo -e "\n❌ Some tests failed!"
fi

# Optional: Run the simple test script too
echo -e "\n3. Running simple curl tests..."
./test_proxy.sh

echo -e "\n==========================================="
echo "Test run complete!"

exit $TEST_EXIT_CODE