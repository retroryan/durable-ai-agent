# Monty Python Streaming Workflow Demo

This document demonstrates the Monty Python infinite loop workflow with Server-Sent Events (SSE) streaming.

## Overview

The MontyPythonWorkflow is a demonstration workflow that:
- Runs in an infinite loop until signaled to stop
- Sleeps for a random duration (5-30 seconds) in each iteration
- Returns a random Monty Python quote after each sleep
- Provides real-time progress updates via SSE streaming
- Supports graceful termination via Temporal signals

## Quick Start

### 1. Start the Services

```bash
docker-compose up
```

This starts:
- Temporal server (port 8080)
- API server (port 8000)
- Worker process

### 2. Start the Streaming Workflow

Using curl:
```bash
curl -X POST http://localhost:8000/monty/stream
```

Using httpie:
```bash
http --stream POST localhost:8000/monty/stream
```

### 3. Monitor Progress

You'll see real-time SSE events like:

```json
data: {"event": "workflow_started", "workflow_id": "monty-python-abc123", "timestamp": "2025-01-19T10:30:15"}

data: {"event": "progress_update", "progress": 10, "status": "iteration_1_sleeping_for_15_seconds", "elapsed": 1.5, "iteration": 1, "quotes_delivered": 0, "current_quote": null, "timestamp": "2025-01-19T10:30:16"}

data: {"event": "progress_update", "progress": 100, "status": "delivered_quote_1", "elapsed": 15.2, "iteration": 1, "quotes_delivered": 1, "current_quote": "Nobody expects the Spanish Inquisition!", "timestamp": "2025-01-19T10:30:30"}
```

### 4. Stop the Workflow

Send a stop signal:
```bash
curl -X POST http://localhost:8000/workflow/{workflow_id}/signal/stop
```

Replace `{workflow_id}` with the ID from the workflow_started event.

## Example Python Client

```python
import httpx
import json
import asyncio

async def stream_monty_workflow():
    async with httpx.AsyncClient() as client:
        workflow_id = None
        
        # Start streaming
        async with client.stream('POST', 'http://localhost:8000/monty/stream') as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    event = json.loads(line[6:])
                    
                    if event['event'] == 'workflow_started':
                        workflow_id = event['workflow_id']
                        print(f"Workflow started: {workflow_id}")
                    
                    elif event['event'] == 'progress_update':
                        if event.get('current_quote'):
                            print(f"Iteration {event['iteration']}: {event['current_quote']}")
                        else:
                            print(f"Progress: {event['progress']}%")
                    
                    # Stop after 3 quotes
                    if event.get('quotes_delivered', 0) >= 3:
                        break
        
        # Stop the workflow
        if workflow_id:
            await client.post(f'http://localhost:8000/workflow/{workflow_id}/signal/stop')
            print(f"Stopped workflow: {workflow_id}")

# Run the client
asyncio.run(stream_monty_workflow())
```

## JavaScript/Browser Example

```javascript
const eventSource = new EventSource('http://localhost:8000/monty/stream', {
    method: 'POST'
});

let workflowId = null;

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.event) {
        case 'workflow_started':
            workflowId = data.workflow_id;
            console.log(`Workflow started: ${workflowId}`);
            break;
            
        case 'progress_update':
            if (data.current_quote) {
                console.log(`Quote ${data.quotes_delivered}: "${data.current_quote}"`);
            } else {
                console.log(`Progress: ${data.progress}%`);
            }
            break;
            
        case 'workflow_completed':
            console.log('Workflow completed:', data.result);
            eventSource.close();
            break;
    }
};

// Stop after 30 seconds
setTimeout(async () => {
    if (workflowId) {
        await fetch(`http://localhost:8000/workflow/${workflowId}/signal/stop`, {
            method: 'POST'
        });
        eventSource.close();
    }
}, 30000);
```

## Integration Tests

Run the integration tests:

```bash
# Run all streaming tests
poetry run pytest integration_tests/test_streaming_monty.py -v

# Run specific test
poetry run pytest integration_tests/test_streaming_monty.py::TestMontyPythonStreaming::test_streaming_workflow -v
```

## Monitoring in Temporal UI

1. Open http://localhost:8080
2. Look for workflows with IDs starting with `monty-python-`
3. Click on a workflow to see:
   - Execution history
   - Current state via queries
   - Signal history

## Architecture Notes

### Workflow Design

The MontyPythonWorkflow demonstrates:
- **Infinite loops** - Runs until signaled to stop
- **Inline activities** - Sleep logic implemented directly in workflow
- **Query handlers** - Real-time state inspection
- **Signal handlers** - Graceful termination

### Streaming Design

The SSE implementation provides:
- **Real-time updates** - Progress events every 500ms
- **Structured events** - JSON-formatted event data
- **Connection management** - Automatic cleanup on completion
- **Error handling** - Graceful error reporting

## Troubleshooting

### No Events Received

Check if services are running:
```bash
docker-compose ps
```

### Connection Refused

Ensure API is accessible:
```bash
curl http://localhost:8000/health
```

### Workflow Not Found

Check Temporal UI for workflow status:
```bash
open http://localhost:8080
```

## Future Enhancements

1. **Batch Operations** - Start/stop multiple workflows
2. **Custom Quotes** - Allow users to provide their own quotes
3. **Persistence** - Store workflow history
4. **Analytics** - Track quote popularity
5. **WebSocket Support** - Bidirectional communication