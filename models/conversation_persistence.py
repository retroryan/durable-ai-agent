from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Any, List
from datetime import datetime

from models.conversation import ConversationState


class ExportedMessage(BaseModel):
    """Exported message format with validation"""
    actor: str
    content: str
    timestamp: str  # ISO format string
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('timestamp')
    def validate_timestamp_format(cls, v):
        """Ensure timestamp is in ISO format"""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("Timestamp must be in ISO format")
        return v


class ExportedConversation(BaseModel):
    """Exported conversation with metadata and validation"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    messages: List[ExportedMessage] = Field(max_length=100)
    user_context: Dict[str, Any]
    tools_used: List[str]
    export_timestamp: str
    version: str = Field(default="1.0")
    
    @field_validator('export_timestamp')
    def validate_export_timestamp(cls, v):
        """Ensure export timestamp is valid"""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("Export timestamp must be in ISO format")
        return v


def export_conversation_state(state: ConversationState) -> ExportedConversation:
    """Export conversation state for external storage with validation"""
    # Convert last 50 messages
    exported_messages = [
        ExportedMessage(
            actor=msg.actor,
            content=msg.content,
            timestamp=msg.timestamp.isoformat(),
            metadata=msg.metadata
        )
        for msg in state.messages[-50:]
    ]
    
    return ExportedConversation(
        messages=exported_messages,
        user_context=state.user_context,
        tools_used=list(set(state.tools_used[-20:])),  # Recent unique tools
        export_timestamp=datetime.now().isoformat()
    )


def create_conversation_summary_message(state: ConversationState) -> str:
    """Create a summary message for starting new conversations"""
    summary = f"""Previous conversation summary:
    - Messages exchanged: {len(state.messages)}
    - Key topics: {', '.join(state.user_context.get('topics', ['general discussion']))}
    - Tools used: {', '.join(set(state.tools_used[-10:]))}
    - User preferences: {state.user_context}
    """
    return summary