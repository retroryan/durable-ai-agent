#!/usr/bin/env python3
"""Run all integration tests.

This script runs the simplified integration test suite consisting of:
1. MCP Connection Tests - Test STDIO and HTTP connections to MCP servers
2. API E2E Tests - Test complete workflows through the API

All tests are direct Python programs (not pytest) for simplicity.

Usage:
    python integration_tests/run_integration_tests.py              # Run all tests
    python integration_tests/run_integration_tests.py --mcp-only   # Run only MCP connection tests
    python integration_tests/run_integration_tests.py --api-only   # Run only API E2E tests
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


def run_direct_python_test(test_file):
    """Run a single direct Python test file and return success status."""
    print(f"\n{'='*60}")
    print(f"Running {test_file.name}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(test_file)], cwd=project_root, capture_output=False
    )

    return result.returncode == 0


def main():
    """Run all integration tests."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run integration tests")
    parser.add_argument(
        "--mcp-only", action="store_true", help="Run only MCP connection tests"
    )
    parser.add_argument(
        "--api-only", action="store_true", help="Run only API E2E tests"
    )
    args = parser.parse_args()

    print("Integration Test Runner")
    print("======================")
    print("Running simplified integration test suite")
    print("")

    # Get test directory
    test_dir = Path(__file__).parent

    # Track results
    passed = 0
    failed = 0

    # Define our two test files
    mcp_test = test_dir / "test_mcp_connections.py"
    api_test = test_dir / "test_api_e2e.py"

    # Run MCP connection tests unless --api-only
    if not args.api_only:
        if mcp_test.exists():
            print("Running MCP Connection Tests")
            print("Note: Make sure MCP servers are running with:")
            print("  poetry run python scripts/run_mcp_servers.py")
            print("")
            
            if run_direct_python_test(mcp_test):
                passed += 1
            else:
                failed += 1
        else:
            print(f"Warning: {mcp_test.name} not found")
            failed += 1

    # Run API E2E tests unless --mcp-only
    if not args.mcp_only:
        if api_test.exists():
            print("\nRunning API E2E Tests")
            print("Note: Make sure docker-compose is running with:")
            print("  docker-compose up -d")
            print("")
            
            if run_direct_python_test(api_test):
                passed += 1
            else:
                failed += 1
        else:
            print(f"Warning: {api_test.name} not found")
            failed += 1

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests run:     {passed + failed}")
    print(f"Passed:        {passed}")
    print(f"Failed:        {failed}")

    overall_passed = failed == 0
    print(f"\nOverall:       {'PASSED' if overall_passed else 'FAILED'}")

    # Exit with appropriate code
    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
