#!/usr/bin/env python3
"""
Integration test for the AI tools endpoint with crop-related queries.
Run with: poetry run python integration_tests/test_ai_tools_endpoint.py
"""
import asyncio
import json
import sys
import uuid
from datetime import datetime

from utils.api_client import DurableAgentAPIClient


async def main():
    """Main test function."""
    print("🚀 Starting AI Tools Endpoint Integration Test")
    print(f"📅 Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Crop-related test query
    crop_query = "weather: Are conditions good for planting corn in Ames, Iowa?"
    
    print(f"\n🌽 Testing crop query: '{crop_query}'")
    print("=" * 60)
    
    # Create API client
    async with DurableAgentAPIClient() as client:
        user_name = f"test_user_{uuid.uuid4().hex[:8]}"
        print(f"🔤 User: {user_name}")
        
        try:
            # Step 1: Send the initial message
            print("\n1️⃣ Sending initial message...")
            response = await client.chat(crop_query, user_name=user_name)
            workflow_id = response.get('workflow_id')
            print(f"✅ Workflow started: {workflow_id}")
            print(f"📄 Initial response: {json.dumps(response, indent=2)}")
            
            # Step 2: Wait a bit for the workflow to process
            print("\n⏳ Waiting for workflow to process...")
            await asyncio.sleep(3)
            
            # Get child workflow ID for AI endpoints
            child_workflow_id = f"agentic-ai-weather-{workflow_id}"
            
            # Step 3: Query the AI trajectory early in the process
            print(f"\n2️⃣ Querying AI trajectory early (after 3 seconds)...")
            early_trajectory_response = await client.client.get(f"{client.base_url}/workflow/{child_workflow_id}/ai-trajectory")
            if early_trajectory_response.status_code == 200:
                early_trajectory = early_trajectory_response.json()
                print("📍 Early trajectory snapshot:")
                print(json.dumps(early_trajectory.get('trajectory', {}), indent=2))
            else:
                print("⚠️  Trajectory not available yet")
            
            # Wait more for completion
            await asyncio.sleep(2)
            
            # Step 4: Query the AI tools endpoint
            print(f"\n3️⃣ Querying AI tools endpoint for child workflow: {child_workflow_id}")
            tools_response = await client.client.get(f"{client.base_url}/workflow/{child_workflow_id}/ai-tools")
            tools_response.raise_for_status()
            tools_response = tools_response.json()
            
            print("\n🔧 Tools used in workflow:")
            print(json.dumps(tools_response, indent=2))
            
            # Step 5: Get the full AI state with trajectory
            print(f"\n4️⃣ Querying full AI state with trajectory...")
            ai_state_response = await client.client.get(
                f"{client.base_url}/workflow/{child_workflow_id}/ai-state?include_trajectory=true"
            )
            ai_state_response.raise_for_status()
            ai_state = ai_state_response.json()
            
            print("\n📊 AI Workflow State:")
            print(f"   Status: {ai_state.get('status')}")
            print(f"   Query Count: {ai_state.get('query_count')}")
            print(f"   Current Iteration: {ai_state.get('current_iteration')}")
            print(f"   Execution Time: {ai_state.get('execution_time'):.2f}s")
            print(f"   Tools Used: {', '.join(ai_state.get('tools_used', []))}")
            
            if 'trajectory' in ai_state and ai_state['trajectory']:
                print("\n📍 Final Trajectory:")
                trajectory = ai_state['trajectory']
                # Group by iteration
                iterations = {}
                for key, value in trajectory.items():
                    if '_' in key:
                        prefix, idx = key.rsplit('_', 1)
                        if idx.isdigit():
                            iteration = int(idx)
                            if iteration not in iterations:
                                iterations[iteration] = {}
                            iterations[iteration][prefix] = value
                
                for idx in sorted(iterations.keys()):
                    print(f"\n   Iteration {idx}:")
                    iteration_data = iterations[idx]
                    if 'thought' in iteration_data:
                        print(f"   💭 Thought: {iteration_data['thought']}")
                    if 'tool_name' in iteration_data:
                        print(f"   🔧 Tool: {iteration_data['tool_name']}")
                    if 'tool_args' in iteration_data:
                        print(f"   📝 Args: {json.dumps(iteration_data['tool_args'])}")
                    if 'observation' in iteration_data:
                        obs = iteration_data['observation']
                        if isinstance(obs, str) and len(obs) > 200:
                            obs = obs[:200] + "..."
                        print(f"   👁️  Observation: {obs}")
            
            # Step 6: Verify expected tools were used
            if tools_response and 'tools_used' in tools_response:
                tools_list = tools_response['tools_used']
                print(f"\n📊 Total tools used: {tools_response.get('tool_count', len(tools_list))}")
                print(f"📋 Tools: {', '.join(tools_list)}")
                
                # Check for agricultural tool
                ag_tools = [t for t in tools_list if 'agricultural' in t.lower()]
                if ag_tools:
                    print("✅ Agricultural weather tool was used!")
                    for tool in ag_tools:
                        print(f"   - {tool}")
                else:
                    print("⚠️  No agricultural tools found in the response")
                
                # Check for weather forecast tool
                forecast_tools = [t for t in tools_list if 'forecast' in t.lower()]
                if forecast_tools:
                    print("✅ Weather forecast tool was used!")
                    for tool in forecast_tools:
                        print(f"   - {tool}")
                
            else:
                print("❌ No tools data in response")
                
            # Step 7: Get final parent workflow status
            print(f"\n5️⃣ Getting final parent workflow status...")
            status_response = await client.get_workflow_status(workflow_id)
            
            print("\n📊 Parent Workflow State:")
            print(f"   Workflow ID: {status_response.get('workflow_id')}")
            print(f"   Status: {status_response.get('status')}")
            print(f"   Query Count: {status_response.get('query_count')}")
            
            # Query the parent workflow for more details
            query_response = await client.query_workflow(workflow_id)
            if query_response:
                print(f"\n📋 Parent Workflow Details:")
                print(f"   Event Count: {query_response.get('event_count', 0)}")
                if 'last_response' in query_response:
                    print(f"   Has Last Response: Yes")
                if 'conversation_history' in query_response:
                    print(f"   Conversation History Length: {len(query_response.get('conversation_history', []))}")
            
            # Check if response mentions corn/planting
            last_response = status_response.get("last_response", {})
            response_message = ""
            if isinstance(last_response, dict):
                response_message = last_response.get("message", "").lower()
            elif isinstance(last_response, str):
                response_message = last_response.lower()
            
            if any(word in response_message for word in ["corn", "plant", "crop", "soil", "agricult"]):
                print("🌱 Agricultural information detected in response!")
            
            print(f"\n✅ Test completed successfully!")
            
            return 0
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            return 1


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


if __name__ == "__main__":
    print("🏗️  Durable AI Agent - AI Tools Endpoint Test")
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