#!/usr/bin/env python3
"""
Simple integration test for MCP Proxy.

This is a standalone script that tests the proxy functionality.
Run with: python mcp_proxy/tests/test_mcp_proxy.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx


class MCPProxyTester:
    """Test the MCP Proxy server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0

    async def run_all_tests(self):
        """Run all tests."""
        print("🧪 MCP Proxy Integration Tests")
        print("=" * 50)

        # Create client
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            # Test 1: Health Check
            await self.test_health_check(client)

            # Test 2: Root Endpoint
            await self.test_root_endpoint(client)

            # Test 3: List Tools - All Services
            await self.test_list_tools_all_services(client)

            # Test 4: Invalid Service
            await self.test_invalid_service(client)

            # Test 5: Tool Invocation
            await self.test_tool_invocation(client)

            # Test 6: Multiple Concurrent Requests
            await self.test_concurrent_requests(client)

        # Print summary
        print("\n" + "=" * 50)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}")

        return self.failed == 0

    async def test_health_check(self, client: httpx.AsyncClient):
        """Test health endpoint."""
        print("\n1️⃣ Testing health endpoint...")
        try:
            response = await client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert "services" in data

            print(f"   ✅ Health check passed")
            print(f"   Status: {data['status']}")
            print(f"   Services: {data['services']}")
            self.passed += 1
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            self.failed += 1

    async def test_root_endpoint(self, client: httpx.AsyncClient):
        """Test root endpoint."""
        print("\n2️⃣ Testing root endpoint...")
        try:
            response = await client.get("/")
            assert response.status_code == 200

            data = response.json()
            assert data["name"] == "MCP Weather Proxy"
            assert len(data["services"]) == 3

            print(f"   ✅ Root endpoint passed")
            print(f"   Services available: {data['services']}")
            self.passed += 1
        except Exception as e:
            print(f"   ❌ Root endpoint failed: {e}")
            self.failed += 1

    async def test_list_tools_all_services(self, client: httpx.AsyncClient):
        """Test listing tools from all services."""
        print("\n3️⃣ Testing tool listing for all services...")

        services = ["forecast", "current", "historical"]
        for service in services:
            print(f"\n   Testing {service} service...")
            try:
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                }

                response = await client.post(f"/mcp/{service}", json=request)
                assert response.status_code == 200

                data = response.json()
                assert data.get("jsonrpc") == "2.0"

                # Check if it's a proper response (either result or error)
                if "result" in data:
                    tools = data["result"].get("tools", [])
                    print(f"      ✅ {service}: {len(tools)} tools available")
                    for tool in tools:
                        print(f"         - {tool.get('name', 'unknown')}")
                elif "error" in data:
                    print(f"      ⚠️ {service}: Error response - {data['error']}")

                self.passed += 1
            except Exception as e:
                print(f"      ❌ {service} failed: {e}")
                self.failed += 1

    async def test_invalid_service(self, client: httpx.AsyncClient):
        """Test request to invalid service."""
        print("\n4️⃣ Testing invalid service (should return 404)...")
        try:
            request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

            response = await client.post("/mcp/invalid", json=request)
            assert response.status_code == 404

            print(f"   ✅ Invalid service correctly returned 404")
            self.passed += 1
        except Exception as e:
            print(f"   ❌ Invalid service test failed: {e}")
            self.failed += 1

    async def test_tool_invocation(self, client: httpx.AsyncClient):
        """Test calling tools through the proxy."""
        print("\n5️⃣ Testing tool invocation...")

        # Test cases for each service
        test_cases = [
            {
                "service": "current",
                "tool": "get_current_weather",
                "args": {"location": "Melbourne"},
            },
            {
                "service": "forecast",
                "tool": "get_forecast",
                "args": {"location": "Sydney", "days": 3},
            },
            {
                "service": "historical",
                "tool": "get_historical_weather",
                "args": {"location": "Brisbane", "date": "2024-01-01"},
            },
        ]

        for test in test_cases:
            print(f"\n   Testing {test['service']}.{test['tool']}...")
            try:
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": test["tool"], "arguments": test["args"]},
                }

                response = await client.post(f"/mcp/{test['service']}", json=request)
                assert response.status_code == 200

                data = response.json()
                assert data.get("jsonrpc") == "2.0"

                if "result" in data:
                    print(f"      ✅ Tool call successful")
                    # Try to extract content from result
                    if isinstance(data["result"], dict) and "content" in data["result"]:
                        content = data["result"]["content"]
                        if isinstance(content, list) and len(content) > 0:
                            print(f"      Result: {content[0].get('text', 'No text')}")
                elif "error" in data:
                    print(f"      ⚠️ Tool call error: {data['error']}")

                self.passed += 1
            except Exception as e:
                print(f"      ❌ Tool call failed: {e}")
                self.failed += 1

    async def test_concurrent_requests(self, client: httpx.AsyncClient):
        """Test multiple concurrent requests."""
        print("\n6️⃣ Testing concurrent requests...")

        # Create multiple requests
        requests = []
        for i, service in enumerate(["forecast", "current", "historical"]):
            request = {
                "jsonrpc": "2.0",
                "id": i + 1,
                "method": "tools/list",
                "params": {},
            }
            requests.append((service, request))

        try:
            # Send all requests concurrently
            tasks = [
                client.post(f"/mcp/{service}", json=req) for service, req in requests
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = 0
            for i, (service, _) in enumerate(requests):
                if isinstance(responses[i], Exception):
                    print(f"   ❌ {service}: {responses[i]}")
                else:
                    if responses[i].status_code == 200:
                        success_count += 1
                        print(f"   ✅ {service}: Success")
                    else:
                        print(f"   ❌ {service}: Status {responses[i].status_code}")

            if success_count == len(requests):
                print(f"   ✅ All concurrent requests succeeded")
                self.passed += 1
            else:
                print(f"   ❌ Some concurrent requests failed")
                self.failed += 1

        except Exception as e:
            print(f"   ❌ Concurrent test failed: {e}")
            self.failed += 1


async def main():
    """Run the tests."""
    tester = MCPProxyTester()

    print("🚀 Starting MCP Proxy tests...")
    print("Make sure the proxy server is running on http://localhost:8000")
    print("")

    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        print("Make sure the MCP Proxy server is running!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
