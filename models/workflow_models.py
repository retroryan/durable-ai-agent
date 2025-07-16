from pydantic import BaseModel, Field


class WorkflowStatus(BaseModel):
    """Structured workflow status information"""
    is_processing: bool
    should_end: bool
    message_count: int = Field(ge=0)
    pending_messages: int = Field(ge=0)
    interaction_count: int = Field(ge=0)