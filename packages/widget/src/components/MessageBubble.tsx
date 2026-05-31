import React from 'react';
import { Message } from 'cc-chatiq-core';

interface MessageBubbleProps {
  message: Message;
}

const styles = {
  systemContainer: {
    display: 'flex',
    justifyContent: 'center',
    margin: '10px 0',
    width: '100%'
  } as React.CSSProperties,
  systemBubble: {
    background: 'rgba(255, 255, 255, 0.05)',
    color: '#94a3b8',
    fontSize: '11px',
    padding: '6px 12px',
    borderRadius: '12px',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    textAlign: 'center',
    maxWidth: '85%',
    letterSpacing: '0.02em'
  } as React.CSSProperties,
  container: {
    display: 'flex',
    flexDirection: 'column',
    margin: '12px 0',
    width: '100%'
  } as React.CSSProperties,
  roleTag: {
    fontSize: '10px',
    fontWeight: 600,
    color: '#64748b',
    marginBottom: '4px',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  } as React.CSSProperties,
  bubble: {
    color: '#ffffff',
    padding: '10px 14px',
    maxWidth: '75%',
    wordBreak: 'break-word',
    fontSize: '14px',
    lineHeight: '1.45',
    position: 'relative'
  } as React.CSSProperties,
  messageText: {
    marginBottom: '4px'
  } as React.CSSProperties,
  timestamp: {
    fontSize: '9px',
    color: 'rgba(255, 255, 255, 0.45)',
    textAlign: 'right',
    marginTop: '2px',
    userSelect: 'none'
  } as React.CSSProperties
};

const formatTime = (isoString: string) => {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch (e) {
    return '';
  }
};

const getRoleLabel = (role: string) => {
  switch (role) {
    case 'customer': return 'You';
    case 'ai': return 'CC-ChatIQ AI';
    case 'agent': return 'Agent';
    case 'system': return 'System';
    default: return role;
  }
};

const getContainerStyle = (isCustomer: boolean): React.CSSProperties => ({
  ...styles.container,
  alignItems: isCustomer ? 'flex-end' : 'flex-start'
});

const getRoleTagStyle = (isCustomer: boolean): React.CSSProperties => ({
  ...styles.roleTag,
  marginLeft: isCustomer ? '0' : '4px',
  marginRight: isCustomer ? '4px' : '0'
});

const getBubbleStyle = (isCustomer: boolean): React.CSSProperties => ({
  ...styles.bubble,
  background: isCustomer 
    ? 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' 
    : 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
  borderRadius: isCustomer ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
  boxShadow: isCustomer 
    ? '0 4px 12px rgba(37, 99, 235, 0.15)' 
    : '0 4px 12px rgba(0, 0, 0, 0.15)',
  border: isCustomer 
    ? '1px solid rgba(255, 255, 255, 0.1)' 
    : '1px solid rgba(255, 255, 255, 0.05)'
});

export const MessageBubble: React.FC<MessageBubbleProps> = React.memo(({ message }) => {
  const isCustomer = message.role === 'customer';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div style={styles.systemContainer}>
        <div style={styles.systemBubble}>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div style={getContainerStyle(isCustomer)}>
      <span style={getRoleTagStyle(isCustomer)}>
        {getRoleLabel(message.role)}
      </span>
      <div style={getBubbleStyle(isCustomer)}>
        <div style={styles.messageText}>{message.content}</div>
        <div style={styles.timestamp}>
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';
