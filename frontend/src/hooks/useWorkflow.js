import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { MESSAGE_ROLES } from '../constants/messageRoles';

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

/**
 * Custom hook for managing workflow conversations with Temporal backend.
 * 
 * This hook handles:
 * - Sending messages to workflows
 * - Polling for responses with deduplication
 * - Managing conversation state
 * - Ending and resetting conversations
 * 
 * The key innovation is using sequential message IDs from the backend
 * to prevent duplicate messages when polling. Each message has a unique
 * incrementing ID, and we only display messages with IDs we haven't seen.
 */
export function useWorkflow() {
  const [workflowId, setWorkflowId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [userName] = useState(generateUserName());
  const pollingIntervalRef = useRef(null);
  // Track the highest message ID we've seen to prevent duplicates
  const lastSeenMessageIdRef = useRef(0);

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
      role: MESSAGE_ROLES.USER,
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

      // Don't add initial response here - let polling handle all messages  
      console.log('[useWorkflow] Message sent, polling will handle responses');

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
    if (!workflowId) {
      return;
    }

    console.log('[useWorkflow] Starting polling for workflow:', workflowId);

    // Start polling
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const status = await api.getStatus(workflowId);
        console.log('[useWorkflow] Poll status:', status);
        setWorkflowStatus(status.status);
        
        // Check conversation history for new messages
        // The backend sends the last 10 messages with sequential IDs
        if (status.conversation_history && status.conversation_history.length > 0) {
          const newMessages = [];
          
          // Process each message in the conversation history
          for (const msg of status.conversation_history) {
            console.log('[useWorkflow] Processing message:', { 
              id: msg.id, 
              role: msg.role, 
              lastSeenId: lastSeenMessageIdRef.current,
              expectedRole: MESSAGE_ROLES.AGENT 
            });
            
            // Only add AGENT messages with IDs higher than what we've seen
            // User messages are already displayed locally
            if (msg.id > lastSeenMessageIdRef.current && msg.role === MESSAGE_ROLES.AGENT) {
              console.log('[useWorkflow] New agent message found:', msg.id, msg.content);
              
              // Map backend message format to frontend format
              const frontendMessage = {
                id: generateId(),
                content: msg.content,
                role: MESSAGE_ROLES.AGENT,
                timestamp: msg.timestamp || new Date().toISOString(),
                backendId: msg.id  // Keep reference to backend ID for debugging
              };
              newMessages.push(frontendMessage);
            }
            
            // Always update our tracking of the highest ID we've seen
            // This includes user messages so we don't get stuck
            if (msg.id > lastSeenMessageIdRef.current) {
              lastSeenMessageIdRef.current = msg.id;
            }
          }
          
          // Add all new messages at once to avoid multiple renders
          if (newMessages.length > 0) {
            setMessages(prev => [...prev, ...newMessages]);
            setIsLoading(false);
          }
        }
        
        // Update loading state based on whether we're waiting for a response
        const pendingPrompts = status.pending_prompts || 0;
        const isProcessing = status.is_processing || false;
        if (pendingPrompts > 0 || isProcessing) {
          setIsLoading(true);
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
  }, [workflowId, messages]);

  // Reset conversation
  const resetConversation = useCallback(async () => {
    // End the current workflow if it exists
    if (workflowId) {
      try {
        await api.endChat(workflowId);
        console.log('[useWorkflow] Ended chat for workflow:', workflowId);
      } catch (err) {
        console.error('Failed to end chat:', err);
      }
    }
    
    // Clear state for new conversation
    setWorkflowId(null);
    setMessages([]);
    setIsLoading(false);
    setError(null);
    setWorkflowStatus(null);
    lastSeenMessageIdRef.current = 0;
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
  }, [workflowId]);

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