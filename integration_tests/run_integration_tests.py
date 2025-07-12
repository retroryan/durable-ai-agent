#!/usr/bin/env python3
"""Run all integration tests.

This script runs both pytest-based API integration tests and direct Python MCP tests.

The project has two types of integration tests:
1. API Integration Tests (pytest-based) - Test API endpoints and workflow functionality
2. MCP Integration Tests (direct Python programs) - Test MCP client functionality

MCP tests are direct Python programs (not pytest) to avoid complexity and issues
with async test runners and connection pooling. We want to keep it this way
because:
1. Complex async handling and event loop conflicts with MCP clients
2. Connection pooling issues when running multiple tests
3. Fixture lifecycle conflicts with long-lived connections
4. Simpler debugging and error messages
5. Direct control over test execution and cleanup

Usage:
    python integration_tests/run_integration_tests.py              # Run all tests
    python integration_tests/run_integration_tests.py --no-http    # Skip HTTP MCP tests
    python integration_tests/run_integration_tests.py --no-api     # Skip API tests
    python integration_tests/run_integration_tests.py --mcp-only   # Run only MCP tests
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
else:
    print(f"No .env file found at {env_path}, using defaults")


def run_pytest_tests(test_dir):
    """Run pytest-based integration tests."""
    print(f"\n{'='*60}")
    print("Running API Integration Tests (pytest)")
    print("=" * 60)

    # Run pytest with verbose output
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"],
        cwd=project_root,
    )

    return result.returncode == 0


def run_direct_python_test(test_file):
    """Run a single direct Python test file and return success status."""
    print(f"\n{'='*60}")
    print(f"Running {test_file.name}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(test_file)], cwd=test_file.parent, capture_output=False
    )

    return result.returncode == 0


def main():
    """Run all integration tests."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument(
        "--no-http", action="store_true", help="Skip HTTP-based MCP integration tests"
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Skip API integration tests (pytest-based)",
    )
    parser.add_argument(
        "--mcp-only", action="store_true", help="Run only MCP tests (skip API tests)"
    )
    args = parser.parse_args()

    print("Integration Test Runner")
    print("======================")
    print("Running both pytest-based API tests and direct Python MCP tests.")

    # Get test directory
    test_dir = Path(__file__).parent

    # Track results
    api_passed = False
    mcp_passed = 0
    mcp_failed = 0
    mcp_skipped = 0

    # Run API tests (pytest-based) unless skipped
    if args.mcp_only or args.no_api:
        print("\nSkipping API integration tests")
        api_passed = True  # Don't count as failure
    else:
        print("\nRunning API integration tests...")
        api_url = os.getenv("API_URL", "http://localhost:8000")
        print(f"API tests will use server at: {api_url}")
        api_passed = run_pytest_tests(test_dir)

    # Find direct Python test files (MCP tests)
    direct_test_files = []
    for test_file in sorted(test_dir.glob("test_*.py")):
        # Skip pytest-based tests and the runner itself
        if (
            test_file.name in ["test_api_endpoints.py", "test_workflow_integration.py"]
            or test_file.name == "run_integration_tests.py"
        ):
            continue
        direct_test_files.append(test_file)

    # Separate HTTP and non-HTTP MCP tests
    http_tests = [f for f in direct_test_files if "http" in f.name.lower()]
    other_tests = [f for f in direct_test_files if "http" not in f.name.lower()]

    print(f"\nFound {len(direct_test_files)} MCP test files:")
    print(f"  - {len(other_tests)} non-HTTP tests")
    print(f"  - {len(http_tests)} HTTP tests")

    # Run non-HTTP MCP tests
    print(f"\n{'='*60}")
    print("Running MCP Integration Tests (direct Python)")
    print("=" * 60)

    for test_file in other_tests:
        if run_direct_python_test(test_file):
            mcp_passed += 1
        else:
            mcp_failed += 1

    # Run HTTP MCP tests unless --no-http is specified
    if args.no_http:
        print("\nSkipping HTTP MCP tests (--no-http flag specified)")
        mcp_skipped += len(http_tests)
    else:
        print("\nRunning HTTP MCP tests (use --no-http to skip)...")
        mcp_url = os.getenv("MCP_FORECAST_SERVER_URL", "http://localhost:7778/mcp")
        print(f"HTTP tests will use MCP server at: {mcp_url}")
        for test_file in http_tests:
            if run_direct_python_test(test_file):
                mcp_passed += 1
            else:
                mcp_failed += 1

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if not (args.mcp_only or args.no_api):
        print(f"API Tests:     {'PASSED' if api_passed else 'FAILED'}")

    print(f"MCP Tests:")
    print(f"  Passed:      {mcp_passed}")
    print(f"  Failed:      {mcp_failed}")
    print(f"  Skipped:     {mcp_skipped}")
    print(f"  Total:       {len(direct_test_files)}")

    overall_passed = api_passed and mcp_failed == 0
    print(f"\nOverall:       {'PASSED' if overall_passed else 'FAILED'}")

    # Exit with appropriate code
    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
