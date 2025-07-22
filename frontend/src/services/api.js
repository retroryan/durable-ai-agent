// Simplified API client for durable-ai-agent
// In production (Docker), nginx will proxy requests, so we use relative URLs
// In development, Vite proxy handles it, so we also use relative URLs
const API_URL = import.meta.env.VITE_API_URL || '';

// Default timeout in milliseconds (120 seconds for demo)
const DEFAULT_TIMEOUT = import.meta.env.VITE_API_TIMEOUT ? parseInt(import.meta.env.VITE_API_TIMEOUT) : 120000;

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
      response.status
    );
  }
  return response.json();
}

function createFetchWithTimeout(timeout = DEFAULT_TIMEOUT) {
  return async (url, options = {}) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      return response;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new ApiError(`Request timeout after ${timeout}ms`, 408);
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  };
}

const fetchWithTimeout = createFetchWithTimeout();

export const api = {
  async sendMessage(message, workflowId = null, userName = null, timeout = DEFAULT_TIMEOUT) {
    const customFetch = timeout !== DEFAULT_TIMEOUT ? createFetchWithTimeout(timeout) : fetchWithTimeout;
    const response = await customFetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        message, 
        workflow_id: workflowId,
        user_name: userName
      })
    });
    return handleResponse(response);
  },
  
  async getStatus(workflowId, timeout = DEFAULT_TIMEOUT) {
    const customFetch = timeout !== DEFAULT_TIMEOUT ? createFetchWithTimeout(timeout) : fetchWithTimeout;
    const response = await customFetch(`${API_URL}/workflow/${workflowId}/status`);
    return handleResponse(response);
  },

  async queryWorkflow(workflowId, timeout = DEFAULT_TIMEOUT) {
    const customFetch = timeout !== DEFAULT_TIMEOUT ? createFetchWithTimeout(timeout) : fetchWithTimeout;
    const response = await customFetch(`${API_URL}/workflow/${workflowId}/query`);
    return handleResponse(response);
  }
};