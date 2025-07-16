from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class ConversationSummary(BaseModel):
    """Summary statistics for a conversation"""
    total_messages: int = Field(ge=0)
    user_messages: int = Field(ge=0)
    agent_messages: int = Field(ge=0)
    tools_used: List[str]
    duration: Optional[float] = Field(default=None, ge=0)
    
    @field_validator('user_messages', 'agent_messages')
    def validate_message_counts(cls, v, values):
        if 'total_messages' in values.data and v > values.data['total_messages']:
            raise ValueError("Component message count exceeds total")
        return v