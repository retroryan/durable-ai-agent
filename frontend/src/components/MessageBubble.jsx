import { MESSAGE_ROLES, MESSAGE_ROLE_CLASSES } from '../constants/messageRoles';

// Individual message display component
export default function MessageBubble({ message }) {
  const isUser = message.role === MESSAGE_ROLES.USER;
  const roleClass = MESSAGE_ROLE_CLASSES[message.role] || MESSAGE_ROLE_CLASSES[MESSAGE_ROLES.AGENT];
  
  return (
    <div className={`message-bubble ${roleClass}`}>
      <div className="message-content">
        {message.content}
      </div>
      {message.timestamp && (
        <div className="message-timestamp">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}