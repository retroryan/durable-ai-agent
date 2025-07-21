export default function WorkflowTraceView({ events, isRunning, workflowId }) {
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getEventMessage = (event) => {
    switch (event.type) {
      case 'workflow_started':
        return `Workflow started: ${event.details.workflow_id}`;
      
      case 'progress_update':
        if (event.details.current_quote) {
          return `Iteration ${event.details.iteration_count}: "${event.details.current_quote}"`;
        }
        return `Iteration ${event.details.iteration_count}: Progress ${event.details.progress}% - ${event.details.status}`;
      
      case 'workflow_completed':
        return `Workflow completed after ${event.details.result?.total_iterations || 0} iterations and ${event.details.result?.total_quotes_delivered || 0} quotes`;
      
      case 'workflow_failed':
        return `Workflow failed: ${event.details.status}`;
      
      default:
        return JSON.stringify(event.details);
    }
  };

  const getLatestStats = () => {
    if (events.length === 0) return null;
    const latestEvent = events[events.length - 1];
    return {
      iterations: latestEvent.details.iteration_count || 0,
      quotes: latestEvent.details.total_quotes_delivered || 0,
      elapsed: latestEvent.details.total_elapsed || 0
    };
  };

  const stats = getLatestStats();

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
          
          {stats && (
            <div className="trace-stats">
              <span>Iterations: {stats.iterations}</span>
              <span className="separator">|</span>
              <span>Quotes Delivered: {stats.quotes}</span>
              <span className="separator">|</span>
              <span>Total Runtime: {stats.elapsed.toFixed(1)} seconds</span>
            </div>
          )}
        </>
      )}
    </div>
  );
}