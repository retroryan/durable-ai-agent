from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import List


class MessageType(Enum):
    USER_QUERY = "user_query"
    TOOL_CONFIRMATION = "tool_confirmation"
    SYSTEM_NOTIFICATION = "system_notification"
    SUMMARY_REQUEST = "summary_request"


class ClassifiedMessage(BaseModel):
    """Message with classification metadata"""
    content: str = Field(min_length=1)
    message_type: MessageType
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    keywords_matched: List[str] = Field(default_factory=list)
    
    @field_validator('content')
    def validate_content_length(cls, v):
        if len(v) > 10000:
            raise ValueError("Message content too long")
        return v


def classify_message(message: str) -> ClassifiedMessage:
    """Classify message type based on content with confidence scoring"""
    lower_msg = message.lower()
    keywords_matched = []
    confidence = 1.0
    
    if lower_msg.startswith("###"):  # System messages
        message_type = MessageType.SYSTEM_NOTIFICATION
        keywords_matched.append("###")
    elif lower_msg in ["yes", "confirm", "proceed", "ok"]:
        message_type = MessageType.TOOL_CONFIRMATION
        keywords_matched.append(lower_msg)
    elif "summary" in lower_msg or "summarize" in lower_msg:
        message_type = MessageType.SUMMARY_REQUEST
        keywords_matched.extend([w for w in ["summary", "summarize"] if w in lower_msg])
        confidence = 0.9  # Slightly less confident for keyword matching
    else:
        message_type = MessageType.USER_QUERY
        confidence = 0.8  # Default classification
    
    return ClassifiedMessage(
        content=message,
        message_type=message_type,
        confidence=confidence,
        keywords_matched=keywords_matched
    )