# Efficient Alternatives to Polling in Temporal Workflows

This document explores more efficient alternatives to the current polling-based approach used in `api/streaming.py` for monitoring workflow progress in real-time.

## Current Approach Analysis

The current implementation uses a polling pattern:
- **Polls `handle.describe()`** every 0.5 seconds to check workflow status
- **Queries workflow progress** when status is "RUNNING"
- **Calls `handle.result()`** only when workflow is "COMPLETED"

While functional, this approach has limitations:
- Unnecessary network calls when nothing has changed
- Fixed polling interval may be too slow for some use cases or too frequent for others
- Resource consumption for long-running workflows
- Latency between actual state changes and client notifications

## Alternative Approaches

### 1. Workflow-Initiated Updates (Push Model)

Instead of polling, have the workflow push updates through activities that notify external systems.

#### Implementation Pattern

```python
# In the workflow
@workflow.defn
class ProgressiveWorkflow:
    def __init__(self):
        self.progress = 0
        self.webhook_url = None
    
    @workflow.run
    async def run(self, webhook_url: str):
        self.webhook_url = webhook_url
        
        for i in range(10):
            self.progress = (i + 1) * 10
            
            # Push progress update
            await workflow.execute_activity(
                send_progress_notification,
                args=[webhook_url, self.progress],
                start_to_close_timeout=timedelta(seconds=5)
            )
            
            # Do actual work
            await workflow.execute_activity(
                do_work_step,
                start_to_close_timeout=timedelta(minutes=1)
            )

# Activity to send notifications
@activity.defn
async def send_progress_notification(webhook_url: str, progress: int):
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json={"progress": progress})
```

**Advantages:**
- Real-time updates exactly when state changes
- No wasted polling requests
- Workflow controls update frequency
- Can batch updates or implement back-pressure

**Disadvantages:**
- Requires webhook endpoint or message queue
- More complex error handling
- Activities add to workflow history

### 2. Temporal Updates with Long Polling

Use Temporal's Update feature to implement a long-polling mechanism where clients wait for updates.

#### Implementation Pattern

```python
# In the workflow
@workflow.defn
class UpdateBasedWorkflow:
    def __init__(self):
        self.progress = 0
        self.update_waiters = []
    
    @workflow.update
    async def wait_for_progress_change(self, last_known_progress: int) -> dict:
        # If progress already changed, return immediately
        if self.progress > last_known_progress:
            return {"progress": self.progress, "status": "in_progress"}
        
        # Otherwise, wait for change
        await workflow.wait_condition(
            lambda: self.progress > last_known_progress,
            timeout=timedelta(seconds=30)  # Long poll timeout
        )
        
        return {"progress": self.progress, "status": "in_progress"}
    
    @workflow.run
    async def run(self):
        for i in range(10):
            self.progress = (i + 1) * 10
            # Progress change will wake up any waiting updates
            await asyncio.sleep(1)  # Simulate work

# Client-side long polling
async def long_poll_workflow_progress(handle: WorkflowHandle):
    last_progress = -1
    
    while True:
        try:
            # This will wait up to 30 seconds for a change
            result = await handle.execute_update(
                "wait_for_progress_change",
                args=[last_progress]
            )
            
            yield result
            
            if result["progress"] >= 100:
                break
                
            last_progress = result["progress"]
            
        except asyncio.TimeoutError:
            # Long poll timeout, retry
            continue
```

**Advantages:**
- Reduces unnecessary polling
- Near real-time updates
- Server-side efficiency
- Works within Temporal's model

**Disadvantages:**
- Still requires some polling (though less frequent)
- Update handlers add complexity
- Client must handle timeouts

### 3. Hybrid Signal-Query Pattern

Use signals to notify when data has changed, combined with queries to fetch the actual data.

#### Implementation Pattern

```python
# In the workflow
@workflow.defn
class SignalQueryWorkflow:
    def __init__(self):
        self.progress = 0
        self.update_version = 0
        self.subscribers = []
    
    @workflow.signal
    def subscribe_to_updates(self, callback_id: str):
        self.subscribers.append(callback_id)
    
    @workflow.query
    def get_progress_if_changed(self, last_version: int) -> dict:
        if self.update_version > last_version:
            return {
                "progress": self.progress,
                "version": self.update_version,
                "changed": True
            }
        return {"changed": False, "version": self.update_version}
    
    async def update_progress(self, new_progress: int):
        self.progress = new_progress
        self.update_version += 1
        
        # Notify subscribers through external mechanism
        for subscriber in self.subscribers:
            await workflow.execute_activity(
                notify_subscriber,
                args=[subscriber, self.update_version],
                start_to_close_timeout=timedelta(seconds=5)
            )

# Client subscribes and waits for notifications
async def efficient_progress_monitoring(handle: WorkflowHandle, subscriber_id: str):
    # Subscribe
    await handle.signal("subscribe_to_updates", subscriber_id)
    
    last_version = -1
    
    # Set up notification receiver (webhook, SSE, WebSocket, etc.)
    async for notification in notification_stream(subscriber_id):
        # Only query when notified of change
        result = await handle.query(
            "get_progress_if_changed",
            args=[last_version]
        )
        
        if result["changed"]:
            yield result
            last_version = result["version"]
```

**Advantages:**
- Queries only when data actually changes
- Minimal network traffic
- Flexible notification mechanisms
- Efficient for multiple subscribers

**Disadvantages:**
- Requires external notification infrastructure
- More complex setup
- Additional activities for notifications

### 4. Event Sourcing with External State Store

Store workflow progress in an external state store that supports change notifications.

#### Implementation Pattern

```python
# In the workflow
@workflow.defn
class EventSourcedWorkflow:
    @workflow.run
    async def run(self, workflow_id: str):
        for i in range(10):
            progress = (i + 1) * 10
            
            # Store progress in external store
            await workflow.execute_activity(
                update_progress_store,
                args=[workflow_id, progress],
                start_to_close_timeout=timedelta(seconds=5)
            )
            
            # Do work
            await asyncio.sleep(1)

# Activity to update external store
@activity.defn
async def update_progress_store(workflow_id: str, progress: int):
    # Could be Redis with pub/sub, PostgreSQL with NOTIFY, etc.
    await redis_client.hset(
        f"workflow:{workflow_id}",
        mapping={"progress": progress, "timestamp": time.time()}
    )
    await redis_client.publish(f"workflow:{workflow_id}:updates", progress)

# Client subscribes to Redis pub/sub
async def stream_from_redis(workflow_id: str):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"workflow:{workflow_id}:updates")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            progress = int(message["data"])
            yield {"progress": progress}
```

**Advantages:**
- True push-based updates
- Scalable to many subscribers
- Can persist progress history
- Works with existing infrastructure

**Disadvantages:**
- Requires external infrastructure
- Additional operational complexity
- Potential consistency issues

### 5. Server-Sent Events (SSE) with Smart Polling

Enhance the current SSE approach with adaptive polling intervals and change detection.

#### Implementation Pattern

```python
class AdaptivePolling:
    def __init__(self, min_interval=0.1, max_interval=5.0, backoff_factor=1.5):
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.backoff_factor = backoff_factor
        self.current_interval = min_interval
        self.last_change_time = time.time()
    
    def record_change(self):
        self.last_change_time = time.time()
        self.current_interval = self.min_interval
    
    def record_no_change(self):
        time_since_change = time.time() - self.last_change_time
        
        # Gradually increase interval when no changes
        self.current_interval = min(
            self.current_interval * self.backoff_factor,
            self.max_interval
        )
    
    def get_interval(self):
        return self.current_interval

async def adaptive_poll_workflow_progress(
    handle: WorkflowHandle,
    query_method: str
) -> AsyncGenerator[Dict[str, Any], None]:
    adaptive = AdaptivePolling()
    last_progress = -1
    last_status = None
    
    while True:
        try:
            description = await handle.describe()
            status = description.status.name if description.status else "UNKNOWN"
            
            status_changed = status != last_status
            last_status = status
            
            if status == "RUNNING":
                progress_info = await handle.query(query_method)
                progress_changed = progress_info.get('progress', -1) != last_progress
                
                if progress_changed or status_changed:
                    adaptive.record_change()
                    last_progress = progress_info['progress']
                    yield create_event(
                        StreamingEvents.PROGRESS_UPDATE,
                        **progress_info
                    )
                else:
                    adaptive.record_no_change()
            
            elif status == "COMPLETED":
                result = await handle.result()
                yield create_event(
                    StreamingEvents.WORKFLOW_COMPLETED,
                    result=result.__dict__ if hasattr(result, '__dict__') else str(result)
                )
                break
            
            elif status in ["FAILED", "TERMINATED", "CANCELLED"]:
                yield create_event(
                    StreamingEvents.WORKFLOW_FAILED,
                    status=status
                )
                break
            
            # Use adaptive interval
            await asyncio.sleep(adaptive.get_interval())
            
        except Exception as e:
            logger.error(f"Error polling workflow: {e}")
            yield create_event(
                StreamingEvents.ERROR,
                error=str(e)
            )
            break
```

**Advantages:**
- Simple enhancement to existing code
- Reduces polling frequency when inactive
- Responsive when changes occur frequently
- No additional infrastructure needed

**Disadvantages:**
- Still polling-based
- May miss brief state changes
- Trade-off between responsiveness and efficiency

## Recommendations

### For Immediate Implementation (Minimal Changes)
**Use Alternative #5 (Adaptive Polling)** - This requires minimal changes to the existing codebase while providing immediate efficiency gains.

### For Medium-Term Enhancement
**Use Alternative #2 (Temporal Updates with Long Polling)** - This leverages Temporal's native features and provides good efficiency without requiring external infrastructure.

### For Long-Term Scalability
**Use Alternative #4 (Event Sourcing with External State Store)** - This provides the most scalable solution for high-volume scenarios with many concurrent workflows and subscribers.

## Performance Comparison

| Approach | Network Calls | Latency | Complexity | Scalability | Infrastructure |
|----------|---------------|---------|------------|-------------|----------------|
| Current Polling | High | 0-500ms | Low | Limited | None |
| Workflow-Initiated | Minimal | Real-time | Medium | Good | Webhook/Queue |
| Update Long Polling | Low | Near real-time | Medium | Good | None |
| Signal-Query Hybrid | Very Low | Real-time | High | Excellent | Notification Service |
| Event Sourcing | Minimal | Real-time | High | Excellent | State Store + Pub/Sub |
| Adaptive Polling | Medium | Variable | Low | Limited | None |

## Implementation Considerations

### 1. Choose Based on Requirements
- **Low latency critical**: Use push-based approaches (1, 3, 4)
- **Simple implementation**: Use adaptive polling (5)
- **Temporal-native**: Use updates with long polling (2)
- **High scale**: Use event sourcing (4)

### 2. Consider Failure Modes
- Push approaches need retry logic and dead letter handling
- Polling approaches are more resilient but less efficient
- External systems add operational complexity

### 3. Monitor and Measure
- Track metrics like notification latency, polling frequency, and resource usage
- A/B test different approaches for your specific use case
- Consider hybrid approaches for different workflow types

### 4. Future Temporal Features
- Keep an eye on Temporal's roadmap for native streaming/subscription features
- The Temporal team has discussed adding native workflow event streaming
- Future versions may provide built-in solutions for this use case

## Conclusion

While the current polling approach works, these alternatives provide paths to better efficiency, lower latency, and improved scalability. The choice depends on your specific requirements for latency, scale, complexity tolerance, and available infrastructure.

Start with adaptive polling for quick wins, then evaluate more sophisticated approaches based on actual usage patterns and requirements.