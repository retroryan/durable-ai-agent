"""Simple workflow that demonstrates Temporal patterns with minimal complexity."""
from collections import deque
from datetime import timedelta
from typing import Deque, List, Optional, Dict, Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from workflows.agentic_ai_workflow import AgenticAIWorkflow
    from models.types import Response
    from models.conversation import ConversationState, Message
    from models.workflow_models import WorkflowStatus


@workflow.defn
class SimpleAgentWorkflow:
    """A simple workflow that calls find_events activity."""

    def __init__(self):
        """Initialize workflow state."""
        self.query_count = 0
        self.conversation_state = ConversationState()
        self.message_queue: Deque[str] = deque()
        self.is_processing = False
        self.should_end = False
        self.user_name = "anonymous"
        
    @workflow.signal
    async def user_message(self, message: str) -> None:
        """Handle incoming user messages asynchronously"""
        workflow.logger.info(f"Received user message: {message[:50]}...")
        if not self.should_end:
            self.message_queue.append(message)
            
    @workflow.signal
    async def end_conversation(self) -> None:
        """Gracefully end the conversation"""
        workflow.logger.info("End conversation signal received")
        self.should_end = True
        
    @workflow.signal
    async def request_summary(self) -> None:
        """Request conversation summary on demand"""
        self.conversation_state.summary_requested = True

    async def _handle_weather_query(self, user_message: str, user_name: str) -> dict:
        """Handle weather queries that start with 'weather:' prefix."""
        # Extract the query after "weather:"
        query = user_message[8:].strip()  # Remove "weather:" prefix and trim whitespace
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Weather prefix detected, extracted query: '{query}'"
        )
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Executing child workflow AgenticAIWorkflow for user '{user_name}'"
        )

        # Execute the child workflow for weather queries
        child_workflow_id = f"agentic-ai-weather-{workflow.info().workflow_id}"
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Child workflow ID: {child_workflow_id}"
        )

        try:
            child_result = await workflow.execute_child_workflow(
                AgenticAIWorkflow,
                args=[
                    query,
                    user_name,
                ],
                id=child_workflow_id,
            )

            workflow.logger.info(
                f"[SimpleAgentWorkflow] Child workflow completed successfully"
            )
            workflow.logger.debug(
                f"[SimpleAgentWorkflow] Child workflow result: {child_result}"
            )

        except Exception as e:
            workflow.logger.error(
                f"[SimpleAgentWorkflow] Error executing child workflow: {e}"
            )
            raise

        # Convert child workflow result to expected format
        activity_result = {
            "message": f"Child workflow result: {child_result.message}",
            "event_count": child_result.event_count,
        }
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Converted child workflow result to activity format"
        )
        return activity_result

    async def _handle_historical_query(self, user_message: str, user_name: str) -> dict:
        """Handle historical weather queries."""
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Historical keyword detected, calling weather_historical_activity"
        )
        return await workflow.execute_activity(
            "weather_historical_activity",
            args=[user_message, user_name],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

    async def _handle_agricultural_query(self, user_message: str, user_name: str) -> dict:
        """Handle agricultural queries."""
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Agriculture keyword detected, calling agricultural_activity"
        )
        return await workflow.execute_activity(
            "agricultural_activity",
            args=[user_message, user_name],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

    async def _handle_default_query(self, user_message: str, user_name: str) -> dict:
        """Handle default queries (backward compatibility with events)."""
        workflow.logger.info(
            f"[SimpleAgentWorkflow] No specific keyword detected, defaulting to find_events_activity"
        )
        return await workflow.execute_activity(
            "find_events_activity",
            args=[user_message, user_name],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
            ),
        )

    @workflow.run
    async def run(self, user_message: str, user_name: str = "anonymous") -> Response:
        """
        Main workflow execution with message processing loop.

        Args:
            user_message: The initial message from the user
            user_name: The name of the user

        Returns:
            Response with event information
        """
        # Log workflow start
        workflow.logger.info(
            f"[SimpleAgentWorkflow] Starting workflow execution - "
            f"Workflow ID: {workflow.info().workflow_id}, User: {user_name}"
        )
        
        # Store user name for use in activities
        self.user_name = user_name
        
        # Process the initial message immediately for backward compatibility
        self.is_processing = True
        response_message = ""
        
        try:
            # Add user message to conversation
            self.conversation_state.add_message("user", user_message)
            self.query_count += 1
            
            # Route to appropriate handler based on content
            if user_message.lower().startswith("weather:"):
                # Use child workflow for weather queries
                child_workflow_id = f"agentic-{workflow.info().workflow_id}-{workflow.info().run_id}"
                result = await workflow.execute_child_workflow(
                    AgenticAIWorkflow,
                    args=[user_message[8:].strip(), self.user_name, self.conversation_state],
                    id=child_workflow_id,
                )
                response_message = result.message if hasattr(result, 'message') else str(result)
                event_count = result.event_count if hasattr(result, 'event_count') else 1
            else:
                # Handle other queries with existing methods
                if "historical" in user_message.lower():
                    activity_result = await self._handle_historical_query(user_message, self.user_name)
                elif "agriculture" in user_message.lower():
                    activity_result = await self._handle_agricultural_query(user_message, self.user_name)
                else:
                    activity_result = await self._handle_default_query(user_message, self.user_name)
                response_message = activity_result["message"]
                event_count = activity_result.get("event_count", 0)
            
            # Add response to conversation
            self.conversation_state.add_message("agent", response_message)
            
        except Exception as e:
            workflow.logger.error(f"Error processing message: {e}")
            response_message = f"Error processing message: {str(e)}"
            event_count = 0
        finally:
            self.is_processing = False
        
        # Return Response for backward compatibility
        return Response(
            message=response_message,
            event_count=event_count,
            query_count=self.query_count,
        )
    
    async def _process_message(self, message: str) -> None:
        """Process a single message through the appropriate workflow"""
        workflow.logger.info(f"Processing message: {message[:50]}...")
        
        # Add user message to conversation
        self.conversation_state.add_message("user", message)
        
        # Increment query counter
        self.query_count += 1
        
        # Route to appropriate handler based on content
        if message.lower().startswith("weather:"):
            # Use child workflow for weather queries
            child_workflow_id = f"agentic-{workflow.info().workflow_id}-{workflow.info().run_id}"
            result = await workflow.execute_child_workflow(
                AgenticAIWorkflow,
                args=[message[8:].strip(), self.user_name, self.conversation_state],  # Remove "weather:" prefix and pass conversation state
                id=child_workflow_id,
            )
            # Extract message from AgenticAIWorkflow result
            response_message = result.message if hasattr(result, 'message') else str(result)
        else:
            # Handle other queries with existing methods
            if "historical" in message.lower():
                activity_result = await self._handle_historical_query(message, self.user_name)
            elif "agriculture" in message.lower():
                activity_result = await self._handle_agricultural_query(message, self.user_name)
            else:
                activity_result = await self._handle_default_query(message, self.user_name)
            response_message = activity_result["message"]
        
        # Add response to conversation
        self.conversation_state.add_message("agent", response_message)
    
    def _prepare_final_response(self) -> str:
        """Prepare final response when conversation ends"""
        total_messages = len(self.conversation_state.messages)
        user_messages = len([m for m in self.conversation_state.messages if m.actor == "user"])
        agent_messages = len([m for m in self.conversation_state.messages if m.actor == "agent"])
        
        summary = f"Conversation ended. Total messages: {total_messages} " \
                  f"(User: {user_messages}, Agent: {agent_messages})"
        
        if self.conversation_state.summary_requested and self.conversation_state.messages:
            # Add conversation summary if requested
            recent_topics = self._extract_topics()
            summary += f"\nTopics discussed: {', '.join(recent_topics)}"
        
        return summary
    
    def _extract_topics(self) -> List[str]:
        """Extract main topics from conversation"""
        topics = []
        for msg in self.conversation_state.messages:
            if msg.actor == "user":
                if "weather" in msg.content.lower():
                    topics.append("weather")
                if "historical" in msg.content.lower():
                    topics.append("historical data")
                if "agriculture" in msg.content.lower():
                    topics.append("agriculture")
        return list(set(topics)) or ["general conversation"]

    @workflow.query
    def get_query_count(self) -> int:
        """Query handler to expose workflow state."""
        return self.query_count

    @workflow.query
    def get_status(self) -> str:
        """Query handler to get workflow status."""
        return f"Workflow has processed {self.query_count} queries"
    
    @workflow.query
    def get_conversation_history(self) -> List[Message]:
        """Retrieve full conversation history"""
        return self.conversation_state.messages
    
    @workflow.query
    def get_workflow_status(self) -> WorkflowStatus:
        """Get detailed workflow execution status"""
        return WorkflowStatus(
            is_processing=self.is_processing,
            should_end=self.should_end,
            message_count=len(self.conversation_state.messages),
            pending_messages=len(self.message_queue),
            interaction_count=self.conversation_state.interaction_count
        )
    
    @workflow.query
    def get_current_reasoning(self) -> Dict[str, Any]:
        """Get current React reasoning trajectory"""
        return self.conversation_state.trajectory
