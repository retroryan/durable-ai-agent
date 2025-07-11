import { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import { useWorkflow } from './hooks/useWorkflow';
import './App.css';

export default function App() {
  const [inputValue, setInputValue] = useState('');
  const {
    workflowId,
    messages,
    isLoading,
    error,
    workflowStatus,
    userName,
    sendMessage,
    resetConversation
  } = useWorkflow();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      sendMessage(inputValue);
      setInputValue('');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Durable AI Agent</h1>
        <div className="user-info">
          <span className="user-name">User: {userName}</span>
        </div>
        {workflowId && (
          <div className="workflow-info">
            <span className="workflow-id">Workflow: {workflowId}</span>
            {workflowStatus && (
              <span className="workflow-status">Status: {workflowStatus}</span>
            )}
          </div>
        )}
      </header>

      <main className="app-main">
        <ChatWindow messages={messages} isLoading={isLoading} />
        
        {error && (
          <div className="error-message">
            <span>Error: {error}</span>
            <button onClick={() => window.location.reload()}>Refresh</button>
          </div>
        )}

        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            className="message-input"
          />
          <button 
            type="submit" 
            disabled={isLoading || !inputValue.trim()}
            className="send-button"
          >
            Send
          </button>
        </form>

        {messages.length > 0 && (
          <button 
            onClick={resetConversation}
            className="reset-button"
          >
            New Conversation
          </button>
        )}
      </main>
    </div>
  );
}
