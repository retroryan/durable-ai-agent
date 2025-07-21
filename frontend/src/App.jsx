import { useState, useEffect } from 'react';
import ChatView from './views/ChatView';
import WorkflowTraceView from './views/WorkflowTraceView';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || '';

export default function App() {
  const [currentView, setCurrentView] = useState('chat');
  const [traceEvents, setTraceEvents] = useState([]);
  const [isMontyRunning, setIsMontyRunning] = useState(false);
  const [workflowId, setWorkflowId] = useState(null);
  const [eventSource, setEventSource] = useState(null);

  const startMontyWorkflow = async () => {
    if (eventSource) {
      eventSource.close();
    }

    setIsMontyRunning(true);
    setTraceEvents([]);
    setWorkflowId(null); // Clear any previous workflow ID

    const newEventSource = new EventSource(`${API_URL}/monty/stream`);
    setEventSource(newEventSource);

    newEventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Received event:', data); // Debug log
      
      if (data.event === 'workflow_started') {
        console.log('Setting workflow ID:', data.workflow_id); // Debug log
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
    console.log('Stop button clicked, workflowId:', workflowId); // Debug log
    if (workflowId) {
      try {
        const response = await fetch(`${API_URL}/workflow/${workflowId}/signal/stop`, {
          method: 'POST'
        });
        console.log('Stop response:', response.status); // Debug log
        
        // Close the event source immediately after sending stop signal
        if (eventSource) {
          eventSource.close();
          setEventSource(null);
        }
        
        // Update state to reflect stopped status
        setIsMontyRunning(false);
        
        // Add a stopped event to the trace
        setTraceEvents(prev => [...prev, {
          timestamp: new Date().toISOString(),
          type: 'workflow_stopped',
          details: {
            event: 'workflow_stopped',
            workflow_id: workflowId,
            message: 'Stop signal sent to workflow'
          }
        }]);
      } catch (error) {
        console.error('Error stopping workflow:', error);
      }
    }
  };

  const clearTrace = () => {
    setTraceEvents([]);
    setWorkflowId(null);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

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
          <button 
            onClick={isMontyRunning ? stopMontyWorkflow : startMontyWorkflow}
            className={`action-button ${isMontyRunning ? 'stop-monty' : 'start-monty'}`}
          >
            {isMontyRunning ? 'Stop Monty' : 'Start Monty'}
          </button>
          {currentView === 'workflow-trace' && (
            <button 
              onClick={clearTrace}
              className="action-button clear-trace"
            >
              Clear
            </button>
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
}