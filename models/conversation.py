"""Conversation models for managing chat history."""

from pydantic import BaseModel, Field, computed_field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import uuid


class ConversationMessage(BaseModel):
    """Complete conversation turn including request and response."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # User request
    user_message: str
    user_timestamp: datetime
    
    # Agent response (populated after processing)
    agent_message: Optional[str] = None
    agent_timestamp: Optional[datetime] = None
    
    # Processing metadata
    tools_used: Optional[List[str]] = None
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None
    
    @computed_field
    @property
    def is_complete(self) -> bool:
        """Check if this conversation turn has been processed."""
        return self.agent_message is not None or self.error is not None
    
    @computed_field
    @property
    def is_error(self) -> bool:
        """Check if this conversation turn resulted in an error."""
        return self.error is not None


class ConversationState(BaseModel):
    """Current state of the conversation."""
    messages: List[ConversationMessage]
    is_processing: bool
    current_message_id: Optional[str]


class ConversationUpdate(BaseModel):
    """Incremental update for efficient frontend sync."""
    new_messages: List[ConversationMessage]
    updated_messages: List[ConversationMessage]
    is_processing: bool
    current_message_id: Optional[str]
    last_seen_message_id: Optional[str]