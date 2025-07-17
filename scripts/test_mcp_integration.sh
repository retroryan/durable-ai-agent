#!/bin/bash
# Script to run MCP integration tests with Docker in mock mode

set -e

echo "🚀 Starting MCP Integration Tests with Docker"
echo "=========================================="

# Ensure TOOLS_MOCK is exported
export TOOLS_MOCK=true

echo "📝 Environment:"
echo "   TOOLS_MOCK=$TOOLS_MOCK"
echo ""

# Function to check if services are running
check_services() {
    echo "🔍 Checking services..."
    
    # Check API
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API server is running"
    else
        echo "❌ API server is not running"
        return 1
    fi
    
    # Check Temporal
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo "✅ Temporal UI is accessible"
    else
        echo "⚠️  Temporal UI is not accessible (service may still be running)"
    fi
    
    # Check Weather Proxy
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Weather proxy is running"
    else
        echo "⚠️  Weather proxy is not running (using individual services)"
    fi
    
    return 0
}

# Function to start services
start_services() {
    echo "🐳 Starting Docker services with weather proxy..."
    TOOLS_MOCK=true docker-compose --profile weather_proxy up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Wait for API to be ready
    echo "🔄 Waiting for API server..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ API server is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
    echo ""
}

# Function to run tests
run_tests() {
    echo ""
    echo "🧪 Running MCP integration tests..."
    echo "=========================================="
    
    # Run E2E tests
    echo ""
    echo "1️⃣ Running MCP Tools E2E Test..."
    echo "-----------------------------------"
    poetry run python integration_tests/test_mcp_tools_e2e.py
    E2E_RESULT=$?
    
    # Run Weather Flow tests
    echo ""
    echo "2️⃣ Running MCP Weather Flow Test..."
    echo "-----------------------------------"
    poetry run python integration_tests/test_mcp_weather_flow.py
    FLOW_RESULT=$?
    
    # Run general weather API tests
    echo ""
    echo "3️⃣ Running General Weather API Test..."
    echo "-----------------------------------"
    poetry run python integration_tests/test_weather_api.py
    API_RESULT=$?
    
    # Summary
    echo ""
    echo "=========================================="
    echo "📊 Test Summary:"
    echo "   MCP E2E Test: $([ $E2E_RESULT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
    echo "   MCP Flow Test: $([ $FLOW_RESULT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
    echo "   General API Test: $([ $API_RESULT -eq 0 ] && echo '✅ PASSED' || echo '❌ FAILED')"
    
    # Return overall result
    if [ $E2E_RESULT -eq 0 ] && [ $FLOW_RESULT -eq 0 ] && [ $API_RESULT -eq 0 ]; then
        echo ""
        echo "🎉 All tests passed!"
        return 0
    else
        echo ""
        echo "⚠️  Some tests failed"
        return 1
    fi
}

# Main execution
main() {
    # Parse arguments
    START_SERVICES=false
    STOP_SERVICES=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --start)
                START_SERVICES=true
                shift
                ;;
            --stop)
                STOP_SERVICES=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--start] [--stop]"
                echo "  --start  Start Docker services before running tests"
                echo "  --stop   Stop Docker services after running tests"
                exit 1
                ;;
        esac
    done
    
    # Start services if requested
    if [ "$START_SERVICES" = true ]; then
        start_services
    fi
    
    # Check if services are running
    if ! check_services; then
        echo ""
        echo "⚠️  Services are not running!"
        echo "   Run with --start flag or manually start:"
        echo "   TOOLS_MOCK=true docker-compose --profile weather_proxy up -d"
        exit 1
    fi
    
    # Run tests
    run_tests
    TEST_RESULT=$?
    
    # Stop services if requested
    if [ "$STOP_SERVICES" = true ]; then
        echo ""
        echo "🛑 Stopping Docker services..."
        docker-compose --profile weather_proxy down
    fi
    
    exit $TEST_RESULT
}

# Run main function
main "$@"