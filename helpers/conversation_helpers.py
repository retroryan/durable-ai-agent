from typing import List, Optional
from datetime import datetime
import logging

from models.conversation import Message, ConversationState
from models.conversation_models import ConversationSummary

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manage conversation history within reasonable limits"""
    
    MAX_HISTORY_SIZE = 100  # Keep last 100 messages
    
    def __init__(self, state: ConversationState):
        self.state = state
        self._start_time = datetime.now()
    
    def add_message(self, actor: str, content: str, **metadata) -> None:
        """Add message and maintain history size"""
        self.state.add_message(actor, content, **metadata)
        
        # Trim history if needed
        if len(self.state.messages) > self.MAX_HISTORY_SIZE:
            # Keep the last MAX_HISTORY_SIZE messages
            self.state.messages = self.state.messages[-self.MAX_HISTORY_SIZE:]
            logger.info(
                f"Trimmed conversation history to {self.MAX_HISTORY_SIZE} messages"
            )
    
    def get_recent_context(self, count: int = 10) -> List[Message]:
        """Get recent messages for context"""
        return self.state.messages[-count:]
    
    def get_conversation_summary(self) -> ConversationSummary:
        """Get summary statistics of conversation"""
        return ConversationSummary(
            total_messages=len(self.state.messages),
            user_messages=len([m for m in self.state.messages if m.actor == "user"]),
            agent_messages=len([m for m in self.state.messages if m.actor == "agent"]),
            tools_used=list(set(self.state.tools_used)),
            duration=self._calculate_duration()
        )
    
    def _calculate_duration(self) -> Optional[float]:
        """Calculate conversation duration in seconds"""
        if not self.state.messages:
            return None
        
        # Get first and last message timestamps
        first_timestamp = self.state.messages[0].timestamp
        last_timestamp = self.state.messages[-1].timestamp
        
        # Calculate duration
        duration = (last_timestamp - first_timestamp).total_seconds()
        return duration if duration > 0 else None