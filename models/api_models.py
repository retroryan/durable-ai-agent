from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

from models.types import Message


class SendMessageRequest(BaseModel):
    """Request model for sending messages"""
    message: str = Field(min_length=1, max_length=10000)
    
    @field_validator('message')
    def validate_message_content(cls, v):
        if v.strip() == "":
            raise ValueError("Message cannot be empty")
        return v


class SendMessageResponse(BaseModel):
    """Response model for message sending"""
    status: str
    workflow_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class EndConversationResponse(BaseModel):
    """Response model for ending conversations"""
    status: str
    final_message_count: Optional[int] = None


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history queries"""
    conversation_history: List[Message]
    total_messages: int
    workflow_id: str


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status queries"""
    workflow_id: str
    is_processing: bool
    should_end: bool
    message_count: int
    pending_messages: int
    interaction_count: int


class SummaryRequestResponse(BaseModel):
    """Response model for summary requests"""
    status: str
    summary_requested: bool
    workflow_id: str