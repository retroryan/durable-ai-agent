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
 * Simplified hook - back to basics
 */
export function useWorkflow() {
  const [workflowId, setWorkflowId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [userName] = useState(generateUserName());
  const pollingIntervalRef = useRef(null);
  const seenMessageIds = useRef(new Set());

  // Generate unique message ID
  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Send message to workflow
  const sendMessage = useCallback(async (messageText) => {
    if (!messageText.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage = {
      id: generateId(),
      content: messageText,
      role: MESSAGE_ROLES.USER,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await api.sendMessage(messageText, workflowId, userName);
      
      if (!workflowId && response.workflow_id) {
        setWorkflowId(response.workflow_id);
      }

      setWorkflowStatus(response.status);
    } catch (err) {
      setError(err.message);
      console.error('Failed to send message:', err);
    } finally {
      setIsLoading(false);
    }
  }, [workflowId, userName]);

  // Poll for updates
  useEffect(() => {
    if (!workflowId) return;

    const pollForUpdates = async () => {
      try {
        // Get conversation updates
        const lastSeenId = Array.from(seenMessageIds.current).pop() || null;
        const convResponse = await api.getConversation(workflowId, lastSeenId);
        
        if (convResponse?.conversation_update?.new_messages) {
          const newMessages = [];
          
          for (const msg of convResponse.conversation_update.new_messages) {
            // Add agent messages only (user messages already shown)
            if (msg.agent_message && msg.is_complete && !seenMessageIds.current.has(msg.id)) {
              newMessages.push({
                id: msg.id,
                content: msg.agent_message,
                role: MESSAGE_ROLES.AGENT,
                timestamp: msg.agent_timestamp || new Date().toISOString()
              });
              seenMessageIds.current.add(msg.id);
            }
          }
          
          if (newMessages.length > 0) {
            setMessages(prev => [...prev, ...newMessages]);
          }
        }
        
        // Update loading state
        setIsLoading(convResponse?.conversation_update?.is_processing || false);
        
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    // Poll immediately
    pollForUpdates();

    // Then poll every second
    pollingIntervalRef.current = setInterval(pollForUpdates, 1000);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [workflowId]);

  // Reset conversation
  const resetConversation = useCallback(async () => {
    if (workflowId) {
      try {
        await api.endChat(workflowId);
      } catch (err) {
        console.error('Failed to end chat:', err);
      }
    }
    
    setWorkflowId(null);
    setMessages([]);
    setIsLoading(false);
    setError(null);
    setWorkflowStatus(null);
    seenMessageIds.current.clear();
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