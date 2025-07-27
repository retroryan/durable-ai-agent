# Conversation History Clean-Up Proposal

## Key Principles

1. **No Migration Layers**: Direct implementation changes without backward compatibility layers
2. **No Compatibility Hacks**: Clean, straightforward code without workarounds
3. **Always Use Pydantic**: All data models must be Pydantic classes for validation and serialization
4. **Keep It Simple**: Minimize complexity, prefer clarity over cleverness
5. **Single Source of Truth**: One clear way to manage conversation history

## Current Issues

### 1. Duplicate Message Storage in Signal Handler

**Problem**: The `prompt` signal in `agentic_ai_workflow.py` immediately adds the user message to conversation history:

```python
@workflow.signal
async def prompt(self, message: str):
    self.pending_messages.append(message)
    # Creates Message object and appends to conversation_history
```

This is premature because:
- The agent hasn't processed the message yet
- No response exists at this point
- Creates incomplete conversation entries

### 2. Message Structure Doesn't Match Frontend Needs

**Problem**: Current Message objects store user and agent messages separately:
- User message added on signal receipt
- Agent response added after processing
- Frontend expects complete request/response pairs with proper MessageRole

### 3. Unclear Query API Surface

**Problem**: Multiple query methods exist:
- `state()` - Returns full workflow state including conversation
- `get_conversation_history()` - Returns ConversationHistory object
- `get_latest_response()` - Returns last agent Message

Which one should the API server use? This creates confusion and potential inconsistency.

### 4. Inefficient Frontend Updates

**Problem**: Sending last 10 messages on every poll is wasteful:
- Frontend re-renders unchanged messages
- Network bandwidth wasted on duplicate data
- No way to detect new vs existing messages

## Proposed Solution

### 1. Conversation Message Structure

Create a unified message structure that captures complete interactions:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid

class MessageRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"

class ConversationMessage(BaseModel):
    """Complete conversation turn including request and response"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # User request
    user_message: str
    user_timestamp: datetime
    
    # Agent response (populated after processing)
    agent_message: Optional[str] = None
    agent_timestamp: Optional[datetime] = None
    
    # Processing metadata
    reasoning_trajectory: Optional[Dict[str, Any]] = None
    tools_used: Optional[List[str]] = None
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if this conversation turn has been processed"""
        return self.agent_message is not None or self.error is not None
    
    @property
    def is_error(self) -> bool:
        """Check if this conversation turn resulted in an error"""
        return self.error is not None
```

### 2. Workflow State Management

Update the workflow to use the new structure:

```python
@dataclass
class AgenticAIWorkflow:
    max_iterations: int = 5
    
    def __init__(self):
        self.conversation_messages: List[ConversationMessage] = []
        self.pending_user_message: Optional[str] = None
        self.current_message_id: Optional[str] = None
        self.is_processing: bool = False
    
    @workflow.signal
    async def prompt(self, message: str):
        """Queue a message for processing without storing it yet"""
        self.pending_user_message = message
    
    @workflow.run
    async def run(self) -> str:
        """Main workflow execution"""
        await workflow.wait_condition(lambda: self.pending_user_message is not None)
        
        while True:
            if self.pending_user_message:
                # Create conversation message when we start processing
                conversation_msg = ConversationMessage(
                    user_message=self.pending_user_message,
                    user_timestamp=datetime.utcnow()
                )
                self.current_message_id = conversation_msg.id
                self.conversation_messages.append(conversation_msg)
                self.is_processing = True
                
                try:
                    # Process the message
                    result = await self._process_message(self.pending_user_message)
                    
                    # Update the conversation message with response
                    conversation_msg.agent_message = result.answer
                    conversation_msg.agent_timestamp = datetime.utcnow()
                    conversation_msg.reasoning_trajectory = result.trajectory
                    conversation_msg.tools_used = self._extract_tools_used(result.trajectory)
                    conversation_msg.processing_time_ms = int(
                        (conversation_msg.agent_timestamp - conversation_msg.user_timestamp).total_seconds() * 1000
                    )
                    
                except Exception as e:
                    conversation_msg.error = str(e)
                    conversation_msg.agent_timestamp = datetime.utcnow()
                
                finally:
                    self.pending_user_message = None
                    self.current_message_id = None
                    self.is_processing = False
            
            # Wait for next message
            await workflow.wait_condition(lambda: self.pending_user_message is not None)
```

### 3. Simplified Query API

Provide a single, clear query method for the API server:

```python
class ConversationState(BaseModel):
    """Current state of the conversation"""
    messages: List[ConversationMessage]
    is_processing: bool
    current_message_id: Optional[str]
    
class ConversationUpdate(BaseModel):
    """Incremental update for efficient frontend sync"""
    new_messages: List[ConversationMessage]
    updated_messages: List[ConversationMessage]
    is_processing: bool
    current_message_id: Optional[str]
    last_seen_message_id: Optional[str]

@workflow.query
def get_conversation_state(self) -> ConversationState:
    """Get complete conversation state - use for initial load"""
    return ConversationState(
        messages=self.conversation_messages,
        is_processing=self.is_processing,
        current_message_id=self.current_message_id
    )

@workflow.query
def get_conversation_updates(self, last_seen_message_id: Optional[str] = None) -> ConversationUpdate:
    """Get updates since last seen message - use for polling"""
    if not last_seen_message_id:
        # First request, return all messages
        return ConversationUpdate(
            new_messages=self.conversation_messages,
            updated_messages=[],
            is_processing=self.is_processing,
            current_message_id=self.current_message_id,
            last_seen_message_id=self.conversation_messages[-1].id if self.conversation_messages else None
        )
    
    # Find messages after last_seen_message_id
    new_messages = []
    updated_messages = []
    found_last_seen = False
    
    for msg in self.conversation_messages:
        if found_last_seen:
            new_messages.append(msg)
        elif msg.id == last_seen_message_id:
            found_last_seen = True
            # Check if this message was updated since last seen
            if not msg.is_complete and msg.agent_message:
                updated_messages.append(msg)
    
    return ConversationUpdate(
        new_messages=new_messages,
        updated_messages=updated_messages,
        is_processing=self.is_processing,
        current_message_id=self.current_message_id,
        last_seen_message_id=self.conversation_messages[-1].id if self.conversation_messages else last_seen_message_id
    )
```

### 4. API Server Updates

Update the API server to use the new query methods:

```python
from fastapi import HTTPException
from typing import Optional

class ChatResponse(BaseModel):
    workflow_id: str
    conversation_update: ConversationUpdate

@app.get("/workflow/{workflow_id}/conversation")
async def get_conversation(
    workflow_id: str,
    last_seen_message_id: Optional[str] = None
) -> ChatResponse:
    """Get conversation updates since last seen message"""
    try:
        # Get workflow handle
        handle = await temporal_client.get_workflow_handle(workflow_id)
        
        # Query for updates
        conversation_update = await handle.query(
            "get_conversation_updates",
            last_seen_message_id
        )
        
        return ChatResponse(
            workflow_id=workflow_id,
            conversation_update=conversation_update
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/{workflow_id}/conversation/full")
async def get_full_conversation(workflow_id: str) -> ConversationState:
    """Get complete conversation state - use sparingly"""
    try:
        handle = await temporal_client.get_workflow_handle(workflow_id)
        return await handle.query("get_conversation_state")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 5. Frontend Integration Pattern

The frontend can now efficiently update:

```typescript
interface ConversationUpdate {
  new_messages: ConversationMessage[];
  updated_messages: ConversationMessage[];
  is_processing: boolean;
  current_message_id: string | null;
  last_seen_message_id: string | null;
}

class ConversationManager {
  private lastSeenMessageId: string | null = null;
  private messages: Map<string, ConversationMessage> = new Map();
  
  async pollForUpdates(workflowId: string) {
    const response = await fetch(
      `/workflow/${workflowId}/conversation?last_seen_message_id=${this.lastSeenMessageId || ''}`
    );
    const data: ConversationUpdate = await response.json();
    
    // Add new messages
    data.new_messages.forEach(msg => {
      this.messages.set(msg.id, msg);
    });
    
    // Update existing messages (e.g., pending -> complete)
    data.updated_messages.forEach(msg => {
      this.messages.set(msg.id, msg);
    });
    
    // Update last seen
    if (data.last_seen_message_id) {
      this.lastSeenMessageId = data.last_seen_message_id;
    }
    
    // Render only changed messages
    this.renderUpdates(data.new_messages, data.updated_messages);
  }
}
```

## Implementation Steps

1. **Create New Models** (30 min)
   - Add `ConversationMessage`, `ConversationState`, `ConversationUpdate` to `models/`
   - Update imports in workflow

2. **Update Workflow** (1 hour)
   - Refactor `AgenticAIWorkflow` to use new message structure
   - Remove duplicate message storage in signal handler
   - Implement new query methods

3. **Update Activities** (30 min)
   - Ensure activities return data compatible with new structure
   - Update trajectory handling

4. **Update API Server** (30 min)
   - Add new conversation endpoints
   - Deprecate old query endpoints
   - Update response models

5. **Testing** (1 hour)
   - Unit tests for new models
   - Integration tests for conversation flow
   - Test incremental updates

## Benefits

1. **Cleaner Architecture**
   - Single message object per conversation turn
   - Clear separation between pending and processed messages
   - No duplicate storage

2. **Better Performance**
   - Frontend only receives new/updated messages
   - Reduced network traffic
   - Efficient rendering

3. **Improved Developer Experience**
   - Single clear API for conversation state
   - Pydantic validation throughout
   - Self-documenting models

4. **Frontend Compatibility**
   - Messages maintain proper roles
   - Complete request/response pairs
   - Unique IDs for tracking

## Migration Notes

Since we're following the "no migration layers" principle:
1. This is a breaking change
2. Frontend must be updated simultaneously
3. No backward compatibility provided
4. Clean cutover required

## Summary

This proposal simplifies conversation management by:
- Storing complete conversation turns as single objects
- Providing efficient incremental updates
- Using Pydantic models throughout
- Maintaining a single source of truth
- Eliminating redundant message storage

The implementation is straightforward, testable, and aligns with the project's simplicity goals.