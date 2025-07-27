// Simplified API client for durable-ai-agent
// In production (Docker), nginx will proxy requests, so we use relative URLs
// In development, Vite proxy handles it, so we also use relative URLs
const API_URL = import.meta.env.VITE_API_URL || '';

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

export const api = {
  async sendMessage(message, workflowId = null, userName = null) {
    const response = await fetch(`${API_URL}/chat`, {
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
  
  async getStatus(workflowId) {
    const response = await fetch(`${API_URL}/workflow/${workflowId}/status`);
    return handleResponse(response);
  },

  async queryWorkflow(workflowId) {
    const response = await fetch(`${API_URL}/workflow/${workflowId}/query`);
    return handleResponse(response);
  },

  async endChat(workflowId) {
    const response = await fetch(`${API_URL}/workflow/${workflowId}/end-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    return handleResponse(response);
  }
};