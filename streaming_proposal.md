# Streaming Response Implementation Proposal

## Overview

This proposal outlines how to implement streaming responses for long-running queries in the Durable AI Agent system. The goal is to provide real-time feedback to clients during the 35-40+ second processing time using Server-Sent Events (SSE) with a single HTTP request/response cycle.

## Current Architecture

### Current Flow
1. Client sends POST request to `/chat`
2. API starts Temporal workflow
3. API waits for workflow completion (`await handle.result()`)
4. API returns complete response after 35-40+ seconds
5. Client has no visibility during processing

### Pain Points
- Long wait times (35-40+ seconds) with no feedback
- API request timeouts (30 seconds) causing failures
- Poor user experience with no progress indication

## Proposed Solution: Server-Sent Events (SSE)

### Why SSE?
- One-way server-to-client streaming (perfect for status updates)
- Works over standard HTTP (no WebSocket complexity)
- Single request/response cycle
- Built-in reconnection support
- Easy to implement with FastAPI

### New Flow
1. Client sends POST request to `/chat/stream`
2. API starts Temporal workflow asynchronously
3. API returns SSE stream immediately
4. API queries workflow state periodically and streams updates
5. API streams final result when workflow completes
6. Connection closes

## Implementation Details

### 1. API Layer Changes (`api/`)

#### New Streaming Endpoint
```python
# api/main.py
from fastapi import Response
from fastapi.responses import StreamingResponse
import asyncio
import json

@app.post("/chat/stream")
async def chat_stream(input_data: WorkflowInput):
    """Stream workflow execution status and results."""
    
    async def event_generator():
        # Start workflow
        workflow_id = input_data.workflow_id or f"durable-agent-{uuid.uuid4()}"
        
        # Send initial event
        yield f"data: {json.dumps({'event': 'workflow_started', 'workflow_id': workflow_id})}\n\n"
        
        # Start workflow without waiting
        handle = await workflow_service.start_workflow_async(
            input_data.message,
            workflow_id,
            input_data.user_name or "anonymous"
        )
        
        # Poll workflow state
        start_time = time.time()
        last_status = None
        
        while True:
            try:
                # Query workflow state
                description = await handle.describe()
                status = description.status.name if description.status else "UNKNOWN"
                
                # Query custom workflow state
                if status == "RUNNING":
                    try:
                        # For AgenticAIWorkflow
                        if "agentic-ai" in workflow_id:
                            details = await handle.query(AgenticAIWorkflow.get_workflow_details)
                            yield f"data: {json.dumps({
                                'event': 'progress_update',
                                'status': status,
                                'iteration': details.get('current_iteration', 0),
                                'tools_used': details.get('tools_used', []),
                                'elapsed_time': time.time() - start_time
                            })}\n\n"
                        else:
                            # For SimpleAgentWorkflow
                            query_count = await handle.query(SimpleAgentWorkflow.get_query_count)
                            status_msg = await handle.query(SimpleAgentWorkflow.get_status)
                            yield f"data: {json.dumps({
                                'event': 'progress_update',
                                'status': status,
                                'query_count': query_count,
                                'status_message': status_msg,
                                'elapsed_time': time.time() - start_time
                            })}\n\n"
                    except Exception as e:
                        logger.warning(f"Could not query workflow state: {e}")
                
                # Check if workflow completed
                if status in ["COMPLETED", "FAILED", "TERMINATED", "CANCELLED"]:
                    if status == "COMPLETED":
                        result = await handle.result()
                        yield f"data: {json.dumps({
                            'event': 'workflow_completed',
                            'result': {
                                'message': result.message,
                                'event_count': result.event_count
                            },
                            'total_time': time.time() - start_time
                        })}\n\n"
                    else:
                        yield f"data: {json.dumps({
                            'event': 'workflow_failed',
                            'status': status,
                            'error': 'Workflow did not complete successfully'
                        })}\n\n"
                    break
                
                # Send heartbeat every 5 seconds
                if time.time() - start_time > 5:
                    yield f"data: {json.dumps({'event': 'heartbeat', 'elapsed_time': time.time() - start_time})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"
                break
            
            # Wait before next poll
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )
```

#### WorkflowService Updates
```python
# api/services/workflow_service.py
async def start_workflow_async(
    self,
    message: str,
    workflow_id: str,
    user_name: str = "anonymous"
) -> WorkflowHandle:
    """Start workflow without waiting for result."""
    return await self.client.start_workflow(
        SimpleAgentWorkflow.run,
        args=[message, user_name],
        id=workflow_id,
        task_queue=self.task_queue,
    )
```

### 2. Workflow Layer Changes (`workflows/`)

#### Enhanced Query Handlers
```python
# workflows/simple_agent_workflow.py
@workflow.query
def get_progress_info(self) -> dict:
    """Get detailed progress information."""
    return {
        "query_count": self.query_count,
        "status": self.current_status,
        "is_processing": self.is_processing,
        "current_activity": self.current_activity
    }

# workflows/agentic_ai_workflow.py
@workflow.query
def get_progress_details(self) -> dict:
    """Get detailed progress including current tool execution."""
    return {
        "current_iteration": self.current_iteration,
        "max_iterations": self.max_iterations,
        "tools_used": self.tools_used,
        "current_tool": self.current_tool,
        "current_phase": self.current_phase,  # "reasoning", "executing", "extracting"
        "trajectory_size": len(self.trajectory)
    }
```

### 3. Frontend Implementation (`frontend/`)

#### React Component with SSE
```typescript
// frontend/src/hooks/useStreamingChat.ts
export const useStreamingChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [progress, setProgress] = useState<ProgressInfo | null>(null);

  const sendMessage = async (message: string) => {
    setIsStreaming(true);
    setProgress({ status: 'starting', elapsed: 0 });

    const eventSource = new EventSource(`${API_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.event) {
        case 'workflow_started':
          setProgress({ 
            status: 'started', 
            workflowId: data.workflow_id,
            elapsed: 0 
          });
          break;
          
        case 'progress_update':
          setProgress({
            status: 'processing',
            iteration: data.iteration,
            tools: data.tools_used,
            elapsed: data.elapsed_time,
            message: `Processing... (${data.tools_used?.length || 0} tools used)`
          });
          break;
          
        case 'workflow_completed':
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: data.result.message,
            timestamp: new Date()
          }]);
          setIsStreaming(false);
          setProgress(null);
          eventSource.close();
          break;
          
        case 'error':
        case 'workflow_failed':
          setProgress({ status: 'error', message: data.error });
          setIsStreaming(false);
          eventSource.close();
          break;
      }
    };

    eventSource.onerror = () => {
      setIsStreaming(false);
      setProgress({ status: 'error', message: 'Connection lost' });
      eventSource.close();
    };
  };

  return { messages, sendMessage, isStreaming, progress };
};
```

#### UI Component
```tsx
// frontend/src/components/StreamingChat.tsx
export const StreamingChat: React.FC = () => {
  const { messages, sendMessage, isStreaming, progress } = useStreamingChat();

  return (
    <div>
      <MessageList messages={messages} />
      
      {progress && (
        <ProgressIndicator
          status={progress.status}
          elapsed={progress.elapsed}
          message={progress.message}
          tools={progress.tools}
        />
      )}
      
      <ChatInput 
        onSend={sendMessage} 
        disabled={isStreaming}
      />
    </div>
  );
};
```

### 4. Integration Tests (`integration_tests/`)

```python
# integration_tests/test_streaming_api.py
import asyncio
import json
import httpx
import pytest

@pytest.mark.asyncio
async def test_streaming_chat():
    """Test SSE streaming endpoint."""
    async with httpx.AsyncClient() as client:
        events = []
        
        async with client.stream(
            'POST',
            'http://localhost:8000/chat/stream',
            json={'message': 'weather: What is the weather in London?'},
            timeout=60.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    event = json.loads(line[6:])
                    events.append(event)
        
        # Verify events
        assert any(e['event'] == 'workflow_started' for e in events)
        assert any(e['event'] == 'progress_update' for e in events)
        assert any(e['event'] == 'workflow_completed' for e in events)
        
        # Verify final result
        completed_event = next(e for e in events if e['event'] == 'workflow_completed')
        assert 'London' in completed_event['result']['message']
```

## Benefits

1. **Immediate Feedback**: Users see progress within milliseconds
2. **No Timeouts**: SSE connections can stay open indefinitely
3. **Detailed Progress**: Show iteration count, tools used, elapsed time
4. **Graceful Degradation**: Can fall back to non-streaming endpoint
5. **Better UX**: Users know the system is working on their query

## Migration Strategy

1. **Phase 1**: Implement streaming endpoint alongside existing `/chat`
2. **Phase 2**: Update frontend to use streaming endpoint
3. **Phase 3**: Add progress tracking to workflows
4. **Phase 4**: Deprecate non-streaming endpoint

## Considerations

### Performance
- Minimal overhead: Only query state every 1 second
- Reuse existing Temporal queries
- No changes to core workflow logic

### Error Handling
- SSE automatically handles reconnection
- Graceful fallback on connection issues
- Clear error events in stream

### Scalability
- SSE is lightweight (long-lived HTTP connection)
- Can handle thousands of concurrent streams
- No additional infrastructure needed

## Alternative Approaches Considered

1. **WebSockets**: Overkill for one-way communication
2. **Long Polling**: Less efficient, multiple requests
3. **gRPC Streaming**: More complex, requires protocol buffers
4. **Webhooks**: Requires client to expose endpoint

## Conclusion

SSE provides the ideal solution for streaming workflow progress with minimal complexity. It requires no new infrastructure, works with existing HTTP, and provides a great user experience during long-running queries.