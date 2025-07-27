/**
 * Message role constants matching the backend MessageRole enum
 * This ensures consistency between frontend and backend
 */
export const MESSAGE_ROLES = {
  USER: 'user',
  AGENT: 'agent',
  SYSTEM: 'system'
};

// CSS class names for message roles
export const MESSAGE_ROLE_CLASSES = {
  [MESSAGE_ROLES.USER]: 'user',
  [MESSAGE_ROLES.AGENT]: 'agent',
  [MESSAGE_ROLES.SYSTEM]: 'system'
};