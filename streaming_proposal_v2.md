# Enhanced Streaming Response Implementation Proposal V2

## Overview

This proposal extends the existing streaming implementation to include a demonstration async workflow that provides real-time progress updates. The system maintains the existing chatbot functionality while adding a separate panel for streaming workflow trace output.

## Architecture Overview

### New Components

1. **MontyPythonWorkflow** (`workflows/monty_python_workflow.py`)
   - Infinite loop workflow with inline activity
   - Sleeps for random duration (5-30 seconds) per iteration
   - Returns random Monty Python quote after each sleep
   - Tracks iteration count and total quotes delivered
   - Provides detailed progress updates during execution
   - Supports graceful termination via signal

2. **Enhanced Streaming UI**
   - Single-page application with tab navigation
   - Chat view maintains existing chatbot functionality
   - Separate Workflow Trace view for monitoring
   - Real-time updates from MontyPythonWorkflow
   - Visual indicator when workflow is running

### UI Layout

The application uses a single-page architecture with client-side routing to switch between views.

#### Chat View (Default)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Durable AI Agent                                   │
│  ┌─────────────┬────────────────┬─────────────────────────────────────┐   │
│  │    Chat     │ Workflow Trace  │              [Start Monty]          │   │
│  └─────────────┴────────────────┴─────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ User: What's the weather in NYC?                                    │  │
│  │                                                                      │  │
│  │ AI: Let me check the weather for you...                            │  │
│  │                                                                      │  │
│  │ [Progress: Analyzing with tools...]                                 │  │
│  │                                                                      │  │
│  │ AI: In NYC, it's currently 45°F with partly cloudy skies.         │  │
│  │ The humidity is 65% and winds are from the northwest at 10 mph.   │  │
│  │                                                                      │  │
│  │ User: How about London?                                             │  │
│  │                                                                      │  │
│  │ AI: _                                                               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Type your message...                                      [Send]     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Status: Monty workflow is running (click Workflow Trace tab to view)      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Workflow Trace View
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Durable AI Agent                                   │
│  ┌─────────────┬────────────────┬─────────────────────────────────────┐   │
│  │    Chat     │ Workflow Trace  │        [Stop Workflow] [Clear]       │   │
│  └─────────────┴────────────────┴─────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Workflow: monty-python-12345                                              │
│  Status: RUNNING                                                           │
│  Started: 2025-01-19 10:30:15                                             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │ Events:                                                              │  │
│  │                                                                      │  │
│  │ 10:30:15 Workflow started                                           │  │
│  │ 10:30:16 Iteration 1: Activity sleeping for 15 seconds...          │  │
│  │ 10:30:17 Iteration 1: Progress 5%                                  │  │
│  │ 10:30:20 Iteration 1: Progress 20%                                 │  │
│  │ 10:30:25 Iteration 1: Progress 45%                                 │  │
│  │ 10:30:30 Iteration 1: Progress 70%                                 │  │
│  │ 10:30:31 Iteration 1: "Nobody expects the Spanish Inquisition!"   │  │
│  │ 10:30:33 Iteration 2: Activity sleeping for 22 seconds...          │  │
│  │ 10:30:40 Iteration 2: Progress 30%                                 │  │
│  │ 10:30:50 Iteration 2: Progress 75%                                 │  │
│  │ 10:30:55 Iteration 2: "It's just a flesh wound."                  │  │
│  │ 10:30:57 Iteration 3: Activity sleeping for 8 seconds...           │  │
│  │ 10:31:05 Iteration 3: "We are the Knights who say... Ni!"         │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Iterations: 3 | Quotes Delivered: 3 | Total Runtime: 50 seconds          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Current Implementation Status

### Backend Implementation ✅ Complete

The backend infrastructure for the Monty Python streaming demo is fully implemented with the following components:

1. **MontyPythonWorkflow** - Infinite loop workflow that generates Monty Python quotes
   - Executes in continuous loop until signaled to stop
   - Uses activity for quote generation (2-5 second intervals)
   - Tracks progress, iterations, and quotes delivered
   - Supports graceful termination via signal
   - Provides real-time state via queries

2. **Streaming Infrastructure** - Dedicated SSE streaming module (`api/streaming.py`)
   - Generic streaming utilities for any workflow
   - Automatic progress polling with configurable intervals
   - Proper SSE event formatting and error handling
   - Reusable components for future streaming features

3. **Integration Tests** - Comprehensive test coverage
   - Tests for workflow execution and streaming
   - Signal handling and graceful termination tests
   - Multiple concurrent workflow tests

### API Endpoints for Frontend

The following endpoints are available for the frontend implementation:

#### Streaming Endpoints

**POST /monty/stream**
- Starts a new Monty Python workflow and streams progress via SSE
- Response: Server-Sent Events stream
- Events:
  - `workflow_started`: Initial event with workflow_id
  - `progress_update`: Progress updates with quote delivery
  - `workflow_completed`: Final event with statistics
  - `workflow_failed`: Error event if workflow fails
  - `error`: General error events

Example SSE event structure:
```json
{
  "event": "progress_update",
  "timestamp": "2025-01-19T10:30:45.123Z",
  "progress": 45,
  "status": "iteration_2_sleeping",
  "iteration_count": 2,
  "total_quotes_delivered": 1,
  "current_quote": "Nobody expects the Spanish Inquisition!",
  "total_elapsed": 15.5,
  "should_exit": false
}
```

#### Workflow Control Endpoints

**POST /workflow/{workflow_id}/signal/stop**
- Sends stop signal to any running workflow
- Request params: `workflow_id` (path parameter)
- Response:
```json
{
  "status": "signal sent",
  "workflow_id": "monty-python-12345",
  "signal": "stop_workflow"
}
```

**GET /workflow/{workflow_id}/status**
- Get current workflow execution status
- Response includes workflow state, start time, and execution status

**GET /workflow/{workflow_id}/query**
- Query workflow state (works with any workflow that has queries)
- For Monty workflow, returns progress information

#### Chat Endpoints (Existing)

**POST /chat**
- Start a new chat conversation
- Request body: `{ "message": "string" }`
- Response includes workflow_id and initial response

**GET /workflow/{workflow_id}/history**
- Get conversation history for chat workflows
- Response includes all messages in the conversation

## Frontend Implementation Design

#### Enhanced App Component with Routing
```tsx
// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { ChatView } from './views/ChatView';
import { WorkflowTraceView } from './views/WorkflowTraceView';

type View = 'chat' | 'workflow-trace';

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('chat');
  const [traceEvents, setTraceEvents] = useState<TraceEvent[]>([]);
  const [isMontyRunning, setIsMontyRunning] = useState(false);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  const startMontyWorkflow = async () => {
    if (eventSource) {
      eventSource.close();
    }

    setIsMontyRunning(true);
    setTraceEvents([]);

    const newEventSource = new EventSource(`${API_URL}/monty/stream`);
    setEventSource(newEventSource);

    newEventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.event === 'workflow_started') {
        setWorkflowId(data.workflow_id);
      }
      
      setTraceEvents(prev => [...prev, {
        timestamp: data.timestamp,
        type: data.event,
        details: data
      }]);

      if (data.event === 'workflow_completed' || data.event === 'workflow_failed') {
        setIsMontyRunning(false);
        newEventSource.close();
        setEventSource(null);
      }
    };

    newEventSource.onerror = () => {
      setIsMontyRunning(false);
      newEventSource.close();
      setEventSource(null);
    };
  };

  const stopMontyWorkflow = async () => {
    if (workflowId) {
      // Send signal to stop workflow
      await fetch(`${API_URL}/workflow/${workflowId}/signal/stop`, {
        method: 'POST'
      });
    }
  };

  const clearTrace = () => {
    setTraceEvents([]);
    setWorkflowId(null);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Durable AI Agent</h1>
        <nav className="tab-navigation">
          <button 
            className={`tab ${currentView === 'chat' ? 'active' : ''}`}
            onClick={() => setCurrentView('chat')}
          >
            Chat
          </button>
          <button 
            className={`tab ${currentView === 'workflow-trace' ? 'active' : ''}`}
            onClick={() => setCurrentView('workflow-trace')}
          >
            Workflow Trace
            {isMontyRunning && <span className="running-indicator">●</span>}
          </button>
          {currentView === 'chat' && (
            <button 
              onClick={startMontyWorkflow}
              disabled={isMontyRunning}
              className="action-button start-monty"
            >
              {isMontyRunning ? 'Monty Running...' : 'Start Monty'}
            </button>
          )}
          {currentView === 'workflow-trace' && isMontyRunning && (
            <>
              <button 
                onClick={stopMontyWorkflow}
                className="action-button stop-workflow"
              >
                Stop Workflow
              </button>
              <button 
                onClick={clearTrace}
                className="action-button clear-trace"
              >
                Clear
              </button>
            </>
          )}
        </nav>
      </header>
      
      <main className="app-content">
        {currentView === 'chat' ? (
          <ChatView isMontyRunning={isMontyRunning} />
        ) : (
          <WorkflowTraceView 
            events={traceEvents}
            isRunning={isMontyRunning}
            workflowId={workflowId}
          />
        )}
      </main>
      
      {currentView === 'chat' && isMontyRunning && (
        <div className="status-bar">
          Status: Monty workflow is running (click Workflow Trace tab to view)
        </div>
      )}
    </div>
  );
};
```

#### Chat View Component
```tsx
// frontend/src/views/ChatView.tsx
import React from 'react';
import { ChatPanel } from '../components/ChatPanel';

interface Props {
  isMontyRunning: boolean;
}

export const ChatView: React.FC<Props> = ({ isMontyRunning }) => {
  return (
    <div className="chat-view">
      <ChatPanel />
    </div>
  );
};
```

#### Workflow Trace View Component
```tsx
// frontend/src/views/WorkflowTraceView.tsx
import React from 'react';

interface TraceEvent {
  timestamp: string;
  type: string;
  details: any;
}

interface Props {
  events: TraceEvent[];
  isRunning: boolean;
  workflowId: string | null;
}

export const WorkflowTraceView: React.FC<Props> = ({ events, isRunning, workflowId }) => {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getEventMessage = (event: TraceEvent) => {
    switch (event.type) {
      case 'workflow_started':
        return `Workflow started: ${event.details.workflow_id}`;
      
      case 'progress_update':
        if (event.details.current_quote) {
          return `Iteration ${event.details.iteration}: "${event.details.current_quote}"`;
        }
        return `Iteration ${event.details.iteration}: Progress ${event.details.progress}% - ${event.details.status}`;
      
      case 'workflow_completed':
        return `Workflow completed after ${event.details.result.total_iterations} iterations and ${event.details.result.total_quotes_delivered} quotes`;
      
      case 'workflow_failed':
        return `Workflow failed: ${event.details.status}`;
      
      default:
        return JSON.stringify(event.details);
    }
  };

  return (
    <div className="trace-view-container">
      {events.length === 0 && !isRunning && (
        <div className="trace-empty">
          <p>No workflow trace available</p>
          <p>Start a Monty workflow from the Chat tab to see trace output</p>
        </div>
      )}
      
      {(events.length > 0 || isRunning) && (
        <>
          <div className="trace-header">
            <div className="workflow-info">
              <div>Workflow: {workflowId || 'Starting...'}</div>
              <div>Status: {isRunning ? 'RUNNING' : 'COMPLETED'}</div>
              {events[0] && (
                <div>Started: {formatTime(events[0].timestamp)}</div>
              )}
            </div>
          </div>
          
          <div className="trace-events-container">
            <h3>Events:</h3>
            <div className="trace-events">
              {events.map((event, index) => (
                <div key={index} className="trace-event">
                  <span className="trace-time">{formatTime(event.timestamp)}</span>
                  <span className="trace-message">{getEventMessage(event)}</span>
                </div>
              ))}
            </div>
          </div>
          
          {events.length > 0 && (
            <div className="trace-stats">
              <span>Iterations: {events[events.length - 1]?.details.iteration || 0}</span>
              <span className="separator">|</span>
              <span>Quotes Delivered: {events[events.length - 1]?.details.quotes_delivered || 0}</span>
              <span className="separator">|</span>
              <span>Total Runtime: {events[events.length - 1]?.details.elapsed?.toFixed(1) || 0} seconds</span>
            </div>
          )}
        </>
      )}
    </div>
  );
};
```

### 4. CSS Styling (`frontend/src/styles.css`)

```css
/* Main Application Layout */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.app-header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header h1 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
}

/* Tab Navigation */
.tab-navigation {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.tab {
  background: none;
  border: none;
  color: #ecf0f1;
  padding: 0.5rem 1rem;
  cursor: pointer;
  border-radius: 4px 4px 0 0;
  transition: all 0.2s;
  position: relative;
}

.tab:hover {
  background-color: #34495e;
}

.tab.active {
  background-color: #ecf0f1;
  color: #2c3e50;
}

.running-indicator {
  color: #2ecc71;
  margin-left: 0.5rem;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Action Buttons */
.action-button {
  margin-left: auto;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.start-monty {
  background-color: #3498db;
  color: white;
}

.start-monty:hover:not(:disabled) {
  background-color: #2980b9;
}

.start-monty:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.stop-workflow {
  background-color: #e74c3c;
  color: white;
  margin-left: 0.5rem;
}

.stop-workflow:hover {
  background-color: #c0392b;
}

.clear-trace {
  background-color: #95a5a6;
  color: white;
  margin-left: 0.5rem;
}

.clear-trace:hover {
  background-color: #7f8c8d;
}

/* Main Content Area */
.app-content {
  flex: 1;
  overflow: hidden;
  background-color: #ecf0f1;
}

/* Status Bar */
.status-bar {
  background-color: #3498db;
  color: white;
  padding: 0.5rem 1rem;
  text-align: center;
  font-size: 0.9rem;
}

/* Chat View */
.chat-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 1rem;
}

/* Workflow Trace View */
.trace-view-container {
  height: 100%;
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

.trace-empty {
  text-align: center;
  padding: 3rem;
  color: #7f8c8d;
}

.trace-header {
  background-color: white;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.workflow-info div {
  margin: 0.25rem 0;
}

.trace-events-container {
  flex: 1;
  background-color: white;
  border-radius: 4px;
  padding: 1rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.trace-events-container h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.trace-events {
  flex: 1;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9rem;
}

.trace-event {
  padding: 0.5rem;
  border-bottom: 1px solid #ecf0f1;
  display: flex;
  align-items: flex-start;
}

.trace-event:last-child {
  border-bottom: none;
}

.trace-time {
  color: #7f8c8d;
  margin-right: 1rem;
  min-width: 80px;
}

.trace-message {
  flex: 1;
  color: #2c3e50;
}

.trace-stats {
  background-color: white;
  padding: 1rem;
  border-radius: 4px;
  margin-top: 1rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.trace-stats .separator {
  margin: 0 1rem;
  color: #bdc3c7;
}
```

## Benefits

1. **Clear Separation**: Chat and workflow trace are visually separated
2. **Real-time Updates**: See workflow progress as it happens
3. **Educational**: Demonstrates Temporal's query capabilities
4. **Entertaining**: Monty Python quotes add humor to the demo
5. **Non-intrusive**: Existing chat functionality remains unchanged
6. **Infinite Loop Demo**: Shows how Temporal handles long-running workflows
7. **Graceful Shutdown**: Demonstrates signal handling for workflow termination

## Technical Highlights

1. **Inline Activities**: Demonstrates workflow logic without separate activity definitions
2. **Query Handlers**: Shows real-time state querying
3. **SSE Streaming**: Efficient server-to-client communication
4. **Parallel UI**: Two independent streaming connections
5. **Progress Tracking**: Granular progress updates every 500ms

## Future Enhancements

1. **Multiple Workflows**: Run multiple Monty workflows simultaneously
2. **Workflow History**: Show past workflow executions
3. **Interactive Controls**: Pause/resume/cancel workflows
4. **Custom Quotes**: Let users add their own quotes
5. **Workflow Comparison**: Compare execution times across runs

## Implementation Plan

### ✅ Phase 1: Backend Implementation (COMPLETE)
- ✅ MontyPythonWorkflow with infinite loop, signals, and queries
- ✅ Streaming endpoint `/monty/stream` with SSE support
- ✅ Signal endpoint `/workflow/{workflow_id}/signal/stop` for graceful shutdown
- ✅ Dedicated streaming infrastructure module (`api/streaming.py`)
- ✅ Worker registration and activity implementation
- ✅ Comprehensive integration tests
- ✅ Full API documentation

### ✅ Phase 2: Frontend Implementation (COMPLETE)
The frontend implementation has been completed with a tabbed interface for chat and workflow trace views:

- ✅ React app structure with client-side routing
- ✅ Tab navigation between Chat and Workflow Trace views
- ✅ ChatView component (maintains existing functionality)
- ✅ WorkflowTraceView component with real-time SSE updates
- ✅ Visual indicators for running workflows (pulsing green dot)
- ✅ Start/Stop workflow controls
- ✅ Responsive design with comprehensive CSS styling

#### Implementation Details

1. **App.jsx** - Main application component with:
   - Tab-based navigation system
   - SSE connection management for Monty Python workflow
   - Start/Stop/Clear controls
   - Status bar showing when workflow is running

2. **ChatView.jsx** - Refactored chat interface:
   - Moved existing chat functionality into a view component
   - Maintains all original features (messaging, workflow status, reset)
   - Clean integration with the new tabbed layout

3. **WorkflowTraceView.jsx** - New trace visualization:
   - Real-time event streaming display
   - Formatted timestamps and event messages
   - Running statistics (iterations, quotes, runtime)
   - Empty state when no workflow is active

4. **App.css** - Enhanced styling:
   - Modern tabbed interface design
   - Animated running indicator
   - Responsive layout for both views
   - Consistent color scheme and typography

### 📋 Phase 3: Deployment & Polish
- [ ] Update docker-compose for production deployment
- [ ] End-to-end testing with frontend
- [ ] Performance optimization for multiple concurrent workflows
- [ ] Additional demo scenarios and documentation

## Conclusion

This enhancement demonstrates Temporal's streaming capabilities while maintaining the existing chat functionality. The side-by-side layout clearly shows the difference between the AI chat workflow and a simple demonstration workflow, making it perfect for demos and educational purposes.