import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '../services/api';

// List of random user names
const RANDOM_NAMES = [
  'Alex_Explorer', 'Sam_Adventurer', 'Chris_Wanderer', 'Jordan_Traveler',
  'Taylor_Seeker', 'Morgan_Dreamer', 'Casey_Pioneer', 'Riley_Navigator',
  'Avery_Discoverer', 'Quinn_Pathfinder', 'Drew_Voyager', 'Blake_Nomad',
  'Cameron_Ranger', 'Skylar_Scout', 'Sage_Trailblazer', 'River_Drifter'
];

// Generate a random user name
const generateUserName = () => {
  const randomIndex = Math.floor(Math.random() * RANDOM_NAMES.length);
  const timestamp = Date.now().toString(36).substr(-4);
  return `${RANDOM_NAMES[randomIndex]}_${timestamp}`;
};

export function useWorkflow() {
  const [workflowId, setWorkflowId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [userName] = useState(generateUserName());
  const pollingIntervalRef = useRef(null);

  // Generate unique message ID
  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Send message to workflow
  const sendMessage = useCallback(async (messageText) => {
    if (!messageText.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message to UI immediately
    const userMessage = {
      id: generateId(),
      content: messageText,
      role: 'user',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      console.log('[useWorkflow] Sending message:', messageText, 'workflowId:', workflowId);
      
      // Send message to API with user name
      const response = await api.sendMessage(messageText, workflowId, userName);
      console.log('[useWorkflow] API response:', response);
      
      // Update workflow ID if this is the first message
      if (!workflowId && response.workflow_id) {
        console.log('[useWorkflow] Setting workflow ID:', response.workflow_id);
        setWorkflowId(response.workflow_id);
      }

      // Add assistant response if available
      if (response.last_response) {
        console.log('[useWorkflow] Initial response available:', response.last_response.message);
        const assistantMessage = {
          id: generateId(),
          content: response.last_response.message,
          role: 'assistant',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        console.log('[useWorkflow] No initial response, will poll for updates');
      }

      setWorkflowStatus(response.status);
    } catch (err) {
      setError(err.message);
      console.error('Failed to send message:', err);
    } finally {
      setIsLoading(false);
    }
  }, [workflowId, userName]);

  // Poll for workflow status updates
  useEffect(() => {
    if (!workflowId || workflowStatus === 'completed' || workflowStatus === 'Completed') {
      return;
    }

    console.log('[useWorkflow] Starting polling for workflow:', workflowId);

    // Start polling
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const status = await api.getStatus(workflowId);
        console.log('[useWorkflow] Poll status:', status);
        setWorkflowStatus(status.status);
        
        // If workflow completed and we have a new response, add it
        if ((status.status === 'completed' || status.status === 'Completed') && status.last_response) {
          console.log('[useWorkflow] Workflow completed with response:', status.last_response.message);
          // Check if we already have this response
          const lastMessage = messages[messages.length - 1];
          if (!lastMessage || lastMessage.content !== status.last_response.message) {
            const assistantMessage = {
              id: generateId(),
              content: status.last_response.message,
              role: 'assistant',
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, assistantMessage]);
          }
          setIsLoading(false);
        } else if (status.status === 'running' || status.status === 'started') {
          console.log('[useWorkflow] Workflow still running, continuing to poll...');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1000); // Poll every second

    // Cleanup
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [workflowId, workflowStatus, messages]);

  // Reset conversation
  const resetConversation = useCallback(() => {
    setWorkflowId(null);
    setMessages([]);
    setIsLoading(false);
    setError(null);
    setWorkflowStatus(null);
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
  }, []);

  return {
    workflowId,
    messages,
    isLoading,
    error,
    workflowStatus,
    userName,
    sendMessage,
    resetConversation
  };
}