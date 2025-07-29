#!/usr/bin/env python3
"""
Multi-turn conversation integration tests.
Run with: poetry run python integration_tests/test_multi_turn.py

This test verifies that the AgenticAIWorkflow correctly handles multi-turn conversations
with proper message ordering, context retention, and tool usage.
"""
import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from integration_tests.utils.api_client import DurableAgentAPIClient


class MultiTurnConversationTest:
    """Test suite for multi-turn conversation capabilities."""
    
    def __init__(self, detailed: bool = False):
        """Initialize test suite with optional detailed output mode."""
        self.detailed = detailed
    
    async def wait_for_agent_message_count(
        self, 
        client: DurableAgentAPIClient, 
        workflow_id: str, 
        target_count: int,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Wait for a specific number of agent messages to appear in the conversation.
        
        Args:
            client: API client
            workflow_id: Workflow ID
            target_count: The number of agent messages to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dict containing the latest agent message content and metadata
        """
        start_time = time.time()
        last_message_count = 0
        
        if self.detailed:
            print(f"⏳ Waiting for {target_count} agent messages", end="", flush=True)
        
        while time.time() - start_time < timeout:
            await asyncio.sleep(2)
            
            # Get conversation state
            conv_state = await client.get_conversation_state(workflow_id)
            messages = conv_state.get("messages", [])
            
            # Count messages that have agent responses
            completed_messages = [msg for msg in messages if msg.get("agent_message")]
            
            # Check if we have new messages
            if len(completed_messages) > last_message_count:
                if self.detailed:
                    print(f"\n   📨 New messages detected: {len(completed_messages) - last_message_count}")
                last_message_count = len(completed_messages)
            elif self.detailed:
                print(".", end="", flush=True)
            
            # Count agent messages (same as completed messages)
            agent_messages = completed_messages
            
            if len(agent_messages) >= target_count:
                elapsed = time.time() - start_time
                latest_agent = agent_messages[-1]
                
                if self.detailed:
                    print(f"\n✅ Found {target_count} agent messages after {elapsed:.2f}s")
                
                # Get tools used for this response
                tools_used = await self.get_tools_for_message(
                    client, workflow_id, latest_agent["id"]
                )
                
                return {
                    "id": latest_agent["id"],
                    "content": latest_agent["agent_message"],
                    "timestamp": latest_agent["agent_timestamp"],
                    "tools_used": tools_used,
                    "elapsed_time": elapsed
                }
        
        # Timeout - show what we did find
        print(f"\n❌ Timeout waiting for {target_count} agent messages")
        print(f"   Total messages: {len(messages)}")
        print(f"   Completed messages: {len(completed_messages)}")
        
        raise TimeoutError(f"{target_count} agent messages not found within {timeout}s")
    
    async def get_tools_for_message(
        self, 
        client: DurableAgentAPIClient, 
        workflow_id: str, 
        message_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get the tools used for a specific message.
        
        For now, returns the current trajectories. In a more sophisticated
        implementation, this would track which tools were used for which message.
        """
        try:
            # Get current trajectories
            trajectories_response = await client.client.get(
                f"{client.base_url}/workflow/{workflow_id}/ai-trajectories"
            )
            trajectories_data = trajectories_response.json()
            
            # Extract tools from trajectories
            trajectories = trajectories_data.get("trajectories", [])
            tools = []
            
            for traj in trajectories:
                if isinstance(traj, dict) and traj.get("tool_name"):
                    if traj["tool_name"] != "finish":
                        tools.append({
                            "name": traj["tool_name"],
                            "args": traj.get("tool_args", {})
                        })
            
            return tools
        except Exception as e:
            if self.detailed:
                print(f"⚠️  Could not get tools for message: {e}")
            return []
    
    async def send_message(
        self, 
        client: DurableAgentAPIClient, 
        workflow_id: str, 
        message: str
    ) -> bool:
        """Send a message to an existing workflow."""
        try:
            response = await client.client.post(
                f"{client.base_url}/workflow/{workflow_id}/message",
                json={"message": message}
            )
            if response.status_code == 200:
                if self.detailed:
                    print(f"✅ Message sent successfully")
                return True
            else:
                print(f"❌ Failed to send message: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    async def test_basic_multi_turn(self, client: DurableAgentAPIClient) -> bool:
        """Test basic multi-turn conversation flow."""
        print("\n" + "="*80)
        print("🧪 TEST: Basic Multi-Turn Conversation")
        print("="*80)
        
        # Create workflow
        user_name = f"farmer_{datetime.now().strftime('%H%M%S')}"
        print(f"👤 Creating workflow for user: {user_name}")
        
        initial_message = "Hi, I'm a farmer in Fresno, California looking for weather information."
        print(f"📤 Initial message: {initial_message}")
        
        initial_response = await client.chat(
            initial_message,
            user_name=user_name
        )
        workflow_id = initial_response.get("workflow_id")
        
        if not workflow_id:
            print("❌ Failed to create workflow")
            return False
        
        print(f"✅ Workflow created: {workflow_id}")
        
        # Wait for initial greeting
        try:
            greeting = await self.wait_for_agent_message_count(client, workflow_id, 1, timeout=30)
            print(f"\n📝 Initial Response:")
            print("-" * 60)
            print(greeting["content"])
            print("-" * 60)
        except TimeoutError:
            print("❌ Failed to get initial greeting")
            return False
        
        # Test conversation turns
        conversations = [
            {
                "query": "What's the weather forecast for Napa Valley?",
                "expected_agent_count": 2,  # 1 initial + 1 for this query
                "expected_tool": "get_weather_forecast",
                "check_content": ["napa", "forecast", "temperature"]
            },
            {
                "query": "How about the agricultural conditions in Napa Valley?",
                "expected_agent_count": 3,  # 1 initial + 2 for queries
                "expected_tool": "get_agricultural_conditions",
                "check_content": ["agricultural", "soil", "moisture"]
            },
            {
                "query": "What are the agricultural conditions in Sonoma County?",
                "expected_agent_count": 4,  # 1 initial + 3 for queries
                "expected_tool": "get_agricultural_conditions",
                "check_content": ["sonoma", "agricultural", "conditions"]
            }
        ]
        
        for i, conv in enumerate(conversations, 1):
            print(f"\n{'='*60}")
            print(f"Turn {i}: {conv['query']}")
            print("="*60)
            
            # Send message
            if not await self.send_message(client, workflow_id, conv["query"]):
                return False
            
            # Wait for response
            try:
                response = await self.wait_for_agent_message_count(
                    client, 
                    workflow_id, 
                    conv["expected_agent_count"],
                    timeout=30
                )
                
                print(f"\n📝 Response (ID: {response['id']}):")
                print("-" * 60)
                print(response["content"])
                print("-" * 60)
                
                # Verify expected tool was used
                tools_used = [t["name"] for t in response["tools_used"]]
                if conv["expected_tool"] in tools_used:
                    print(f"✅ Expected tool '{conv['expected_tool']}' was used")
                else:
                    print(f"❌ Expected tool '{conv['expected_tool']}' not found")
                    print(f"   Tools used: {tools_used}")
                    return False
                
                # Check content contains expected keywords
                content_lower = response["content"].lower()
                missing_keywords = []
                for keyword in conv["check_content"]:
                    if keyword not in content_lower:
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    print(f"⚠️  Missing expected keywords: {missing_keywords}")
                else:
                    print(f"✅ Response contains expected content")
                    
            except TimeoutError:
                print(f"❌ Failed to get response for turn {i}")
                return False
        
        print("\n✅ Basic multi-turn conversation test passed!")
        return True
    
    async def test_explicit_context(self, client: DurableAgentAPIClient) -> bool:
        """Test multi-turn conversation with explicit context in each message."""
        print("\n" + "="*80)
        print("🧪 TEST: Multi-Turn with Explicit Context")
        print("="*80)
        
        # Create workflow
        user_name = f"vintner_{datetime.now().strftime('%H%M%S')}"
        print(f"👤 Creating workflow for user: {user_name}")
        
        initial_response = await client.chat(
            "I grow grapes in Napa Valley",
            user_name=user_name
        )
        workflow_id = initial_response.get("workflow_id")
        
        if not workflow_id:
            print("❌ Failed to create workflow")
            return False
        
        print(f"✅ Workflow created: {workflow_id}")
        
        # Wait for initial response
        try:
            greeting = await self.wait_for_agent_message_count(client, workflow_id, 1, timeout=30)
            print(f"\n📝 Initial greeting received")
        except TimeoutError:
            print("❌ Failed to get initial response")
            return False
        
        # Ask about weather with explicit location
        print("\n📤 Sending: 'What's the weather forecast for Napa Valley?'")
        if not await self.send_message(client, workflow_id, "What's the weather forecast for Napa Valley?"):
            return False
        
        try:
            response = await self.wait_for_agent_message_count(client, workflow_id, 2, timeout=30)
            print(f"\n📝 Weather Response:")
            print("-" * 60)
            print(response["content"][:300] + "..." if len(response["content"]) > 300 else response["content"])
            print("-" * 60)
            
            # Verify weather tool was used
            tools = response["tools_used"]
            if tools and tools[0]["name"] == "get_weather_forecast":
                print("✅ Weather forecast tool used correctly")
                args = tools[0]["args"]
                lat = float(args.get("latitude", 0))
                lon = float(args.get("longitude", 0))
                if 38.0 < lat < 39.0 and -123.0 < lon < -122.0:
                    print(f"✅ Correct Napa Valley coordinates: ({lat}, {lon})")
            else:
                print("❌ Expected weather forecast tool")
                return False
                
        except TimeoutError:
            print("❌ Failed to get weather response")
            return False
        
        # Ask about grape conditions with explicit context
        print("\n📤 Sending: 'What are the agricultural conditions for grapes in Napa Valley?'")
        if not await self.send_message(client, workflow_id, "What are the agricultural conditions for grapes in Napa Valley?"):
            return False
        
        try:
            response = await self.wait_for_agent_message_count(client, workflow_id, 3, timeout=30)
            print(f"\n📝 Agricultural Response:")
            print("-" * 60)
            print(response["content"][:300] + "..." if len(response["content"]) > 300 else response["content"])
            print("-" * 60)
            
            # Verify agricultural tool was used
            tools = response["tools_used"]
            if tools and "get_agricultural_conditions" in [t["name"] for t in tools]:
                print("✅ Agricultural conditions tool used")
                for tool in tools:
                    if tool["name"] == "get_agricultural_conditions":
                        crop_type = tool["args"].get("crop_type", "").lower()
                        if "grape" in crop_type:
                            print(f"✅ Correct crop type: {crop_type}")
                        break
            else:
                print("❌ Expected agricultural conditions tool")
                return False
                
        except TimeoutError:
            print("❌ Failed to get conditions response")
            return False
        
        print("\n✅ Explicit context test passed!")
        return True
    
    async def test_conversation_flow(self, client: DurableAgentAPIClient) -> bool:
        """Test a natural conversation flow with follow-up questions."""
        print("\n" + "="*80)
        print("🧪 TEST: Natural Conversation Flow")
        print("="*80)
        
        # Create workflow
        user_name = f"grower_{datetime.now().strftime('%H%M%S')}"
        initial_response = await client.chat(
            "Hello, I need help planning irrigation for my vineyard",
            user_name=user_name
        )
        workflow_id = initial_response.get("workflow_id")
        
        if not workflow_id:
            print("❌ Failed to create workflow")
            return False
        
        print(f"✅ Workflow created: {workflow_id}")
        
        # Natural conversation flow
        flow = [
            {
                "query": "Check the weather forecast for Sonoma County",
                "message_id": 4,
                "purpose": "Initial weather check"
            },
            {
                "query": "Will it rain this week in Sonoma County?",
                "message_id": 6,
                "purpose": "Follow-up about precipitation"
            },
            {
                "query": "What about the soil moisture levels in Sonoma County?",
                "message_id": 8,
                "purpose": "Related agricultural question"
            },
            {
                "query": "Based on the weather and soil moisture in Sonoma, should I irrigate today?",
                "message_id": 10,
                "purpose": "Decision-making question"
            }
        ]
        
        for step in flow:
            print(f"\n{'='*60}")
            print(f"🎯 {step['purpose']}")
            print(f"📤 Query: {step['query']}")
            print("="*60)
            
            if not await self.send_message(client, workflow_id, step["query"]):
                return False
            
            try:
                response = await self.wait_for_agent_message_count(
                    client, workflow_id, 
                    step["message_id"] // 2,  # Convert message ID to agent count
                    timeout=30
                )
                
                print(f"\n📝 Response preview:")
                print("-" * 60)
                # Show first 300 chars of response
                preview = response["content"][:300]
                if len(response["content"]) > 300:
                    preview += "..."
                print(preview)
                print("-" * 60)
                
                if response["tools_used"]:
                    print(f"🔧 Tools used: {[t['name'] for t in response['tools_used']]}")
                
            except TimeoutError:
                print(f"❌ Failed to get response")
                return False
        
        # Verify the final response provides irrigation advice
        final_response = response["content"].lower()
        irrigation_keywords = ["irrigate", "irrigation", "water", "moisture"]
        found_keywords = [kw for kw in irrigation_keywords if kw in final_response]
        
        if found_keywords:
            print(f"\n✅ Final response provides irrigation advice: {found_keywords}")
        else:
            print(f"\n⚠️  Final response may not provide clear irrigation advice")
        
        print("\n✅ Natural conversation flow test passed!")
        return True
    
    async def test_conversation_history(self, client: DurableAgentAPIClient) -> bool:
        """Test that conversation history is properly maintained."""
        print("\n" + "="*80)
        print("🧪 TEST: Conversation History Tracking")
        print("="*80)
        
        # Create workflow with initial message
        initial_response = await client.chat("Hi there!")
        workflow_id = initial_response.get("workflow_id")
        
        if not workflow_id:
            print("❌ Failed to create workflow")
            return False
        
        # Send several messages
        messages = [
            "What's the weather in New York?",
            "How about Los Angeles?",
            "Which city is warmer?"
        ]
        
        expected_total_messages = 1 + len(messages)  # Initial + additional messages
        
        for i, msg in enumerate(messages):
            print(f"\n📤 Sending message {i+1}: {msg}")
            if not await self.send_message(client, workflow_id, msg):
                return False
            
            # Wait for response (1 initial + i+1 for this response)
            expected_agent_count = 1 + (i + 1)  # 2, 3, 4...
            try:
                await self.wait_for_agent_message_count(client, workflow_id, expected_agent_count, timeout=30)
            except TimeoutError:
                print(f"❌ Failed to get response {i+1}")
                return False
        
        # Get final conversation state
        print("\n📊 Checking conversation history...")
        conv_state = await client.get_conversation_state(workflow_id)
        messages = conv_state.get("messages", [])
        
        print(f"Total messages in conversation: {len(messages)}")
        
        # Expected: initial message + 3 additional messages = 4 total
        expected_message_count = 1 + 3  # 4
        if len(messages) == expected_message_count:
            print(f"✅ Correct number of conversation messages: {expected_message_count}")
        else:
            print(f"❌ Expected {expected_message_count} messages, got {len(messages)}")
            return False
        
        # Verify message IDs are UUIDs
        message_ids = [msg["id"] for msg in messages]
        all_uuids = all(isinstance(msg_id, str) and len(msg_id) == 36 and '-' in msg_id for msg_id in message_ids)
        if all_uuids:
            print("✅ All message IDs are valid UUIDs")
        else:
            print(f"❌ Some message IDs are not valid UUIDs: {message_ids}")
            return False
        
        # Verify all messages have both user and agent parts (except possibly the last one if still processing)
        completed_count = sum(1 for msg in messages if msg.get("agent_message"))
        if completed_count == len(messages):
            print("✅ All messages have been completed with agent responses")
        else:
            print(f"⚠️  {completed_count}/{len(messages)} messages have agent responses")
        
        # Display conversation summary
        print("\n📜 Conversation Summary:")
        print("-" * 60)
        for msg in messages:
            # Show user message
            user_preview = msg["user_message"][:60] + "..." if len(msg["user_message"]) > 60 else msg["user_message"]
            print(f"[{msg['id']}] 👤 USER : {user_preview}")
            
            # Show agent response if available
            if msg.get("agent_message"):
                agent_preview = msg["agent_message"][:60] + "..." if len(msg["agent_message"]) > 60 else msg["agent_message"]
                print(f"[{msg['id']}] 🤖 AGENT: {agent_preview}")
        print("-" * 60)
        
        print("\n✅ Conversation history test passed!")
        return True
    
    async def run_all_tests(self, client: DurableAgentAPIClient) -> int:
        """Run all multi-turn conversation tests."""
        tests = [
            ("Basic Multi-Turn", self.test_basic_multi_turn),
            # ("Explicit Context", self.test_explicit_context),
            # ("Natural Flow", self.test_conversation_flow),
            # ("History Tracking", self.test_conversation_history),
        ]
        
        passed = 0
        failed = 0
        
        print("\n" + "="*80)
        print("🔄 MULTI-TURN CONVERSATION INTEGRATION TESTS")
        print("="*80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Running: {len(tests)} tests")
        if self.detailed:
            print("🔍 Mode: Detailed output enabled")
        print("="*80)
        
        for test_name, test_func in tests:
            try:
                if await test_func(client):
                    passed += 1
                    print(f"\n✅ PASSED: {test_name}")
                else:
                    failed += 1
                    print(f"\n❌ FAILED: {test_name}")
            except Exception as e:
                failed += 1
                print(f"\n❌ CRASHED: {test_name}")
                print(f"   Error: {e}")
                if self.detailed:
                    import traceback
                    traceback.print_exc()
        
        # Summary
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {(passed / len(tests) * 100):.1f}%")
        print("="*80)
        
        return failed


async def main():
    """Run multi-turn conversation integration tests."""
    parser = argparse.ArgumentParser(
        description="Run multi-turn conversation integration tests",
        epilog="Examples:\n"
               "  poetry run python integration_tests/test_multi_turn.py\n"
               "  poetry run python integration_tests/test_multi_turn.py -d  # Detailed output",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-d", "--detailed",
        action="store_true",
        help="Show detailed output including message tracking"
    )
    
    args = parser.parse_args()
    
    client = DurableAgentAPIClient()
    test_suite = MultiTurnConversationTest(detailed=args.detailed)
    
    # Check API health
    print("🏥 Checking API health...")
    if not await client.health_check():
        print("❌ API is not healthy. Make sure services are running with:")
        print("   docker-compose up")
        sys.exit(1)
    print("✅ API is healthy")
    
    # Run tests
    failed = await test_suite.run_all_tests(client)
    
    # Exit with appropriate code
    sys.exit(failed)


if __name__ == "__main__":
    asyncio.run(main())