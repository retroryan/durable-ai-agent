#!/usr/bin/env python3
"""Integration tests for Monty Python streaming workflow."""
import asyncio
import json
import sys
import time
import httpx
from typing import List, Dict, Any
from utils.api_client import DurableAgentAPIClient


class MontyPythonStreamingTests:
    """Test the Monty Python streaming workflow."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def test_streaming_workflow(self):
        """Test SSE streaming endpoint for Monty Python workflow."""
        print("\n🧪 Testing Monty Python streaming workflow...")
        
        events: List[Dict[str, Any]] = []
        workflow_id = None
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Start streaming
            async with client.stream(
                'POST',
                f'{self.base_url}/monty/stream',
                headers={'Accept': 'text/event-stream'}
            ) as response:
                assert response.status_code == 200, f"Expected 200, got {response.status_code}"
                content_type = response.headers.get('content-type', '')
                print(f"  📋 Content-Type: {content_type}")
                assert 'text/event-stream' in content_type, f"Invalid content type: {content_type}"
                
                # Collect events for up to 40 seconds to ensure we get quotes
                start_time = time.time()
                async for line in response.aiter_lines():
                    if time.time() - start_time > 40:  # Limit test duration
                        break
                        
                    if line.startswith('data: '):
                        try:
                            event = json.loads(line[6:])
                            events.append(event)
                            print(f"  📨 Received event: {event['event']}")
                            
                            # Debug first progress event
                            if event['event'] == 'progress_update' and len([e for e in events if e['event'] == 'progress_update']) == 1:
                                print(f"  🔍 First progress update: {json.dumps(event, indent=2)}")
                            
                            # Capture workflow ID
                            if event['event'] == 'workflow_started':
                                workflow_id = event['workflow_id']
                                print(f"  🆔 Workflow ID: {workflow_id}")
                            
                            # Stop after 2 iterations
                            if event['event'] == 'progress_update' and event.get('iteration_count', 0) >= 2:
                                break
                        except json.JSONDecodeError:
                            pass
        
        # Verify events
        assert len(events) > 0, "No events received"
        
        # Check for expected event types
        event_types = {event['event'] for event in events}
        assert 'workflow_started' in event_types, "Missing workflow_started event"
        assert 'progress_update' in event_types, "Missing progress_update events"
        
        # Verify workflow ID
        assert workflow_id is not None, "No workflow ID received"
        assert workflow_id.startswith('monty-python-'), f"Invalid workflow ID format: {workflow_id}"
        
        # Check progress events
        progress_events = [e for e in events if e['event'] == 'progress_update']
        assert len(progress_events) > 0, "No progress events received"
        
        # Verify progress tracking
        for event in progress_events:
            assert 'progress' in event, "Missing progress field"
            assert 'iteration_count' in event, "Missing iteration_count field"
            assert 'status' in event, "Missing status field"
            assert 0 <= event['progress'] <= 100, f"Invalid progress value: {event['progress']}"
        
        # Check for quotes
        quote_events = [e for e in progress_events if e.get('current_quote')]
        assert len(quote_events) > 0, "No quotes received"
        print(f"  ✅ Received {len(quote_events)} quotes")
        
        # Now stop the workflow
        if workflow_id:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'{self.base_url}/workflow/{workflow_id}/signal/stop'
                )
                assert response.status_code == 200, f"Failed to stop workflow: {response.status_code}"
                result = response.json()
                assert result['status'] == 'signal sent', f"Unexpected status: {result['status']}"
                print(f"  🛑 Workflow stopped successfully")
        
        print("  ✅ Streaming workflow test passed!")
        return True
    
    async def test_signal_stop_workflow(self):
        """Test stopping a workflow via signal."""
        print("\n🧪 Testing workflow stop signal...")
        
        workflow_id = None
        
        # Start workflow first
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                'POST',
                f'{self.base_url}/monty/stream',
                headers={'Accept': 'text/event-stream'}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        try:
                            event = json.loads(line[6:])
                            if event['event'] == 'workflow_started':
                                workflow_id = event['workflow_id']
                                print(f"  🆔 Started workflow: {workflow_id}")
                                break
                        except json.JSONDecodeError:
                            pass
        
        assert workflow_id is not None, "Failed to start workflow"
        
        # Wait a moment for workflow to be running
        print("  ⏳ Waiting for workflow to run...")
        await asyncio.sleep(2)
        
        # Send stop signal
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{self.base_url}/workflow/{workflow_id}/signal/stop'
            )
            assert response.status_code == 200, f"Failed to send stop signal: {response.status_code}"
            result = response.json()
            assert result['status'] == 'signal sent', f"Unexpected status: {result['status']}"
            assert result['workflow_id'] == workflow_id, "Workflow ID mismatch"
            assert result['signal'] == 'stop_workflow', "Wrong signal type"
            print(f"  🛑 Stop signal sent successfully")
        
        print("  ✅ Stop signal test passed!")
        return True
    
    async def test_multiple_concurrent_workflows(self):
        """Test running multiple Monty Python workflows concurrently."""
        print("\n🧪 Testing multiple concurrent workflows...")
        
        workflow_ids = []
        
        async def start_workflow():
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    'POST',
                    f'{self.base_url}/monty/stream',
                    headers={'Accept': 'text/event-stream'}
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith('data: '):
                            try:
                                event = json.loads(line[6:])
                                if event['event'] == 'workflow_started':
                                    return event['workflow_id']
                            except json.JSONDecodeError:
                                pass
            return None
        
        # Start 3 workflows concurrently
        print("  🚀 Starting 3 workflows concurrently...")
        tasks = [start_workflow() for _ in range(3)]
        workflow_ids = await asyncio.gather(*tasks)
        
        # Verify all workflows started
        assert all(wf_id is not None for wf_id in workflow_ids), "Some workflows failed to start"
        assert len(set(workflow_ids)) == 3, "Duplicate workflow IDs detected"
        print(f"  ✅ Started workflows: {workflow_ids}")
        
        # Wait a moment for workflows to be fully running
        await asyncio.sleep(2)
        
        # Stop all workflows
        async def stop_workflow(wf_id):
            try:
                async with httpx.AsyncClient() as client:
                    # First check if workflow exists
                    status_response = await client.get(
                        f'{self.base_url}/workflow/{wf_id}/status'
                    )
                    if status_response.status_code == 404:
                        print(f"  ⚠️  Workflow {wf_id} not found (may have already completed)")
                        return True  # Consider it successful if workflow is gone
                    
                    # Try to stop the workflow
                    response = await client.post(
                        f'{self.base_url}/workflow/{wf_id}/signal/stop'
                    )
                    return response.status_code == 200
            except Exception as e:
                print(f"  ⚠️  Failed to stop workflow {wf_id}: {e}")
                return False
        
        print("  🛑 Stopping all workflows...")
        stop_tasks = [stop_workflow(wf_id) for wf_id in workflow_ids]
        results = await asyncio.gather(*stop_tasks)
        
        # Show which workflows failed
        for i, (wf_id, success) in enumerate(zip(workflow_ids, results)):
            if not success:
                print(f"  ❌ Failed to stop workflow {i+1}: {wf_id}")
            else:
                print(f"  ✅ Successfully stopped workflow {i+1}: {wf_id}")
        
        assert all(results), "Some workflows failed to stop"
        print("  ✅ All workflows stopped successfully")
        
        print("  ✅ Concurrent workflows test passed!")
        return True


def check_services():
    """Check if required services are running."""
    import httpx
    
    print("🔍 Checking services...")

    try:
        # Check API
        response = httpx.get("http://localhost:8000/health", timeout=5.0)
        if response.status_code == 200:
            print("✅ API server is running on port 8000")
        else:
            print("❌ API server returned non-200 status")
            return False
    except Exception as e:
        print("❌ API server is not accessible on port 8000")
        print(f"   Error: {e}")
        print("\n💡 Make sure to run: docker-compose up")
        return False

    return True


async def main():
    """Run all Monty Python streaming tests."""
    print("🎬 Running Monty Python Streaming Integration Tests")
    print("=" * 50)
    
    tests = MontyPythonStreamingTests()
    
    try:
        # Check if API is accessible
        async with DurableAgentAPIClient() as client:
            health = await client.health_check()
            print(f"✅ API Health Check: {health}")
    except Exception as e:
        print(f"❌ API is not accessible: {e}")
        print("   Please ensure the API server is running on http://localhost:8000")
        return 1
    
    all_passed = True
    test_methods = [
        tests.test_streaming_workflow,
        tests.test_signal_stop_workflow,
        tests.test_multiple_concurrent_workflows
    ]
    
    for test in test_methods:
        try:
            await test()
        except AssertionError as e:
            print(f"❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
            all_passed = False
        except Exception as e:
            print(f"❌ Test error: {test.__name__}")
            print(f"   Error: {type(e).__name__}: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    print("🏗️  Durable AI Agent - Monty Python Streaming Test")
    print("=" * 60)

    # Check if services are running
    if not check_services():
        print("\n⚠️  Please start the services before running this test.")
        print("   Run: docker-compose up")
        sys.exit(1)

    print("")

    # Run the async main function
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        sys.exit(1)