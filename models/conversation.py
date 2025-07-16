from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime


class Message(BaseModel):
    """Message model with validation for actor types"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    actor: Literal["user", "agent", "system"]
    content: str = Field(min_length=1, max_length=50000)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    """Conversation state with built-in validation and serialization"""
    messages: List[Message] = Field(default_factory=list)
    trajectory: Dict[str, Any] = Field(default_factory=dict)
    tools_used: List[str] = Field(default_factory=list)
    user_context: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    interaction_count: int = Field(default=0, ge=0)
    summary_requested: bool = False
    
    def add_message(self, actor: Literal["user", "agent", "system"], 
                    content: str, **metadata) -> None:
        """Add a message to the conversation history with validation"""
        message = Message(actor=actor, content=content, metadata=metadata)
        self.messages.append(message)
        self.interaction_count += 1
    
    @field_validator('messages')
    def validate_message_count(cls, v):
        """Ensure we don't exceed reasonable message limits"""
        if len(v) > 1000:
            raise ValueError("Conversation exceeds maximum message limit")
        return v